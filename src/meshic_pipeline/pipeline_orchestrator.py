from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import concurrent.futures
import itertools

import geopandas as gpd
import sys
from tqdm import tqdm

from .config import settings
from .discovery.tile_endpoint_discovery import get_tile_coordinates_for_bounds, get_tile_coordinates_for_grid
from .discovery.enhanced_province_discovery import get_enhanced_tile_coordinates, get_saudi_arabia_tiles, EnhancedProvinceDiscovery
from .downloader.async_tile_downloader import AsyncTileDownloader
from .decoder.mvt_decoder import MVTDecoder
from .geometry.validator import validate_geometries
from .geometry.stitcher import GeometryStitcher
from .persistence.postgis_persister import PostGISPersister


def setup_logging():
    """Configure logging based on settings."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = settings.log_level.value if hasattr(settings.log_level, 'value') else settings.log_level
    
    # Use a basic configuration that can be updated
    logging.basicConfig(level=log_level, format=log_format)
    
    # Get the root logger
    root_logger = logging.getLogger()
    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file, mode='a')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

    # Set the level for the root logger
    root_logger.setLevel(log_level)
    
setup_logging()
logger = logging.getLogger(__name__)


def decode_and_validate_tile(
    tile_coords: Tuple[int, int, int],
    tile_data: bytes,
    layers_to_process: List[str],
    default_crs: str,
) -> List[Tuple[str, gpd.GeoDataFrame]]:
    """
    Worker function to decode a single tile, create GDFs, and validate geometries.
    Designed to be run in a separate process.
    """
    z, x, y = tile_coords
    if not tile_data:
        # Warning logged in main thread to avoid multiprocessing logging complexities.
        return []

    decoder = MVTDecoder(target_crs=default_crs)
    decoded_layers = decoder.decode_bytes(
        tile_data, z=z, x=x, y=y, layers=layers_to_process
    )

    validated_gdfs = []
    for layer_name, features in decoded_layers.items():
        if not features:
            continue

        gdf = gpd.GeoDataFrame(features, geometry="geometry", crs=default_crs)
        gdf = validate_geometries(gdf)

        if not gdf.empty:
            validated_gdfs.append((layer_name, gdf))

    return validated_gdfs


async def run_pipeline(
    aoi_bbox: Tuple[float, float, float, float] = None,
    zoom: int = None,
    layers_override: List[str] | None = None,
    recreate_db: bool = False,
    save_as_temp: str | None = None,
    province: str | None = None,
    strategy: str = "optimal",
    saudi_arabia_mode: bool = False,
) -> None:
    """
    Orchestrates the full pipeline from tile discovery to data persistence.
    
    Args:
        aoi_bbox: Area of interest bounding box
        zoom: Zoom level for tiles
        layers_override: Optional list of layers to process instead of default
        recreate_db: Whether to recreate the database
        save_as_temp: Optional temp table name to save parcels data for delta comparison
        province: Optional province name for enhanced discovery (al_qassim, riyadh, etc.)
        strategy: Discovery strategy ("optimal", "efficient", "comprehensive")
        saudi_arabia_mode: If True, process all Saudi provinces
    """
    layers_to_process = layers_override or settings.layers_to_process
    zoom = zoom or settings.zoom
    
    logger.info("Starting pipeline run for AOI: %s at zoom %d", aoi_bbox or province or "grid", zoom)
    logger.debug("Using settings: %s", settings.model_dump_json(indent=2))

    # Enhanced tile discovery with multiple modes
    if saudi_arabia_mode:
        # Process all Saudi Arabia provinces
        tiles = get_saudi_arabia_tiles(strategy=strategy)
        logger.info("🇸🇦 Saudi Arabia mode: Discovered %d tiles across all provinces", len(tiles))
    elif province:
        # Enhanced province discovery
        tiles = get_enhanced_tile_coordinates(province=province, zoom=zoom, strategy=strategy)
        logger.info("🏛️ Province mode (%s): Discovered %d tiles using %s strategy", province, len(tiles), strategy)
    elif aoi_bbox:
        # Traditional bbox discovery
        tiles = get_tile_coordinates_for_bounds(aoi_bbox, zoom)
        logger.info("📦 Bbox mode: Discovered %d tiles for AOI", len(tiles))
    else:
        # Default grid discovery
        tiles = get_tile_coordinates_for_grid(
            settings.center_x,
            settings.center_y,
            settings.grid_w,
            settings.grid_h,
            zoom,
        )
        logger.info("🔢 Grid mode: Discovered %d tiles for %dx%d grid", len(tiles), settings.grid_w, settings.grid_h)

    # 2. Download tiles with province-specific server
    # Determine the correct tile server based on mode
    if province:
        # Use province-specific server
        tile_server = EnhancedProvinceDiscovery.get_province_server(province)
        tile_base_url = f"https://tiles.suhail.ai/maps/{tile_server}"
        logger.info("🌐 Using province-specific tile server: %s", tile_base_url)
    else:
        # Use default server from settings
        tile_base_url = settings.tile_base_url
        logger.info("🌐 Using default tile server: %s", tile_base_url)
    
    # Create downloader with correct base URL
    async with AsyncTileDownloader(base_url=tile_base_url) as dl:
        raw_tiles = await dl.download_many(tiles)

    # Filter out empty tiles once to avoid re-checking in the loop
    non_empty_tiles = {}
    for (z, x, y), data in raw_tiles.items():
        if data:
            non_empty_tiles[(z, x, y)] = data
        else:
            logger.warning("Tile %d/%d/%d was empty, skipping.", z, x, y)
            
    # Initialize components once
    persister = PostGISPersister(str(settings.database_url))
    stitcher = GeometryStitcher(target_crs=settings.default_crs, persister=persister)
    if recreate_db:
        logger.info("Recreating database: %s", settings.database_url.path)
        persister.recreate_database()

    # 4. Process each layer sequentially to manage memory
    for layer in tqdm(layers_to_process, desc="Processing Layers"):
        logger.info("--- Starting processing for layer: %s ---", layer)
        
        # --- Pass 1: Discover full schema from all tiles ---
        all_columns = set()
        decoded_gdfs_cache = []  # Cache decoded GDFs in memory for the second pass
        
        with concurrent.futures.ProcessPoolExecutor() as executor:
            tasks = [
                (coords, data, [layer], settings.default_crs)
                for coords, data in non_empty_tiles.items()
            ]
            results_iterator = executor.map(decode_and_validate_tile, *zip(*tasks))
            pbar = tqdm(results_iterator, total=len(tasks), desc=f"Pass 1/2: Discovering schema for {layer}", unit="tile")

            for result_list in pbar:
                # Cache the results for the next pass
                decoded_gdfs_cache.append(result_list)
                for _layer_name, gdf in result_list:
                    all_columns.update(gdf.columns)

        if not all_columns:
            logger.warning("Layer '%s': No geometries or columns found after decoding, skipping.", layer)
            logger.info("--- Finished processing for layer: %s ---", layer)
            continue
            
        logger.info("Discovered full schema for layer '%s' with %d columns.", layer, len(all_columns))

        # --- Pass 2: Stitch and Persist using the full schema ---
        id_col = settings.id_column_per_layer.get(layer)
        agg_rules = settings.aggregation_rules_per_layer.get(layer, {})

        # Flatten the cached list of GDFs
        layer_gdfs = [gdf for result_list in decoded_gdfs_cache for _layer_name, gdf in result_list]

        logger.info(
            "Stitching layer '%s' using ID column '%s' and %d aggregation rules.",
            layer, id_col, len(agg_rules)
        )
        
        stitched_gdf = stitcher.stitch_geometries(
            layer_gdfs,
            layer_name=layer,
            id_column=id_col,
            agg_rules=agg_rules,
            tiles=list(non_empty_tiles.keys()),
            known_columns=list(all_columns)  # Pass the definitive schema
        )

        if stitched_gdf.empty:
            logger.warning("Stitching layer '%s' resulted in an empty GeoDataFrame. Skipping.", layer)
            logger.info("--- Finished processing for layer: %s ---", layer)
            continue

        # Save stitched file locally
        out_path = settings.stitched_dir / f"{layer}_stitched.geojson"
        stitched_gdf.to_file(out_path, driver="GeoJSON")
        
        # Persist to PostGIS
        table_name = settings.table_name_mapping.get(layer, layer)
        logger.info(
            "Persisting %d features for layer '%s' to table '%s'",
            len(stitched_gdf), layer, table_name
        )
        
        # Save to temp table if requested and this is the parcels layer
        if save_as_temp and layer == "parcels":
            logger.info(
                "Saving parcels data to temporary table '%s' for delta comparison",
                save_as_temp
            )
            persister.write(
                stitched_gdf, table=save_as_temp, if_exists="replace", chunksize=settings.db_chunk_size
            )
        
        persister.write(
            stitched_gdf, table=table_name, chunksize=settings.db_chunk_size
        )
        logger.info("--- Finished processing for layer: %s ---", layer)

    logger.info("🎉 Pipeline finished successfully. 🎉") 