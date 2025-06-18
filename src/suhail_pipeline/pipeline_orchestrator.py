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
from .discovery.tile_endpoint_discovery import get_tile_coordinates_for_bounds
from .downloader.async_tile_downloader import AsyncTileDownloader
from .decoder.mvt_decoder import MVTDecoder
from .geometry.validator import validate_geometries
from .geometry.stitcher import GeometryStitcher
from .persistence.postgis_persister import PostGISPersister


def setup_logging():
    """Configure logging based on settings."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # Use a basic configuration that can be updated
    logging.basicConfig(level=settings.log_level, format=log_format)
    
    # Get the root logger
    root_logger = logging.getLogger()
    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(settings.log_level)
    console_handler.setFormatter(logging.Formatter(log_format))
    root_logger.addHandler(console_handler)

    # Add file handler if specified
    if settings.log_file:
        file_handler = logging.FileHandler(settings.log_file, mode='a')
        file_handler.setLevel(settings.log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

    # Set the level for the root logger
    root_logger.setLevel(settings.log_level)
    
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

    decoder = MVTDecoder()
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
    aoi_bbox: Tuple[float, float, float, float],
    zoom: int,
    layers_override: List[str] | None = None,
    recreate_db: bool = False,
) -> None:
    """
    Orchestrates the full pipeline from tile discovery to data persistence.
    """
    layers_to_process = layers_override or settings.layers_to_process
    logger.info("Starting pipeline run for AOI: %s at zoom %d", aoi_bbox, zoom)
    logger.debug("Using settings: %s", settings.model_dump_json(indent=2))

    # 1. Discover tiles
    tiles = get_tile_coordinates_for_bounds(aoi_bbox, zoom)
    logger.info("Discovered %d tiles to process at z%d", len(tiles), zoom)

    # 2. Download tiles
    async with AsyncTileDownloader() as dl:
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
        
        # 4a. Decode tiles for the current layer in parallel
        layer_gdfs: List[gpd.GeoDataFrame] = []

        with concurrent.futures.ProcessPoolExecutor() as executor:
            tasks = [
                (coords, data, [layer], settings.default_crs)
                for coords, data in non_empty_tiles.items()
            ]
            
            results_iterator = executor.map(
                decode_and_validate_tile, *zip(*tasks)
            )
            
            # Wrap the iterator with tqdm for a progress bar
            pbar = tqdm(results_iterator, total=len(tasks), desc=f"Decoding {layer}", unit="tile")
            
            # The worker returns a list of (layer_name, gdf). We just need the gdf.
            for result_list in pbar:
                for _layer_name, gdf in result_list:
                    layer_gdfs.append(gdf)

        if not layer_gdfs:
            logger.warning("Layer '%s': No geometries found after decoding, skipping.", layer)
            logger.info("--- Finished processing for layer: %s ---", layer)
            continue
            
        # 4b. Stitch and Persist the current layer
        id_col = settings.id_column_per_layer.get(layer)
        agg_rules = settings.aggregation_rules_per_layer.get(layer, {})

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
        persister.write(
            stitched_gdf, table=table_name, chunksize=settings.db_chunk_size
        )
        logger.info("--- Finished processing for layer: %s ---", layer)

    logger.info("🎉 Pipeline finished successfully. 🎉") 