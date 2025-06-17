from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Tuple

import geopandas as gpd
import sys

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

    # 3. Decode and write temp GeoJSONs
    decoder = MVTDecoder()
    layer_temp_files: Dict[str, List[Path]] = {layer: [] for layer in layers_to_process}

    for (z, x, y), data in raw_tiles.items():
        if not data:
            logger.warning("Tile %d/%d/%d was empty, skipping.", z, x, y)
            continue
        decoded = decoder.decode_bytes(data, z=z, x=x, y=y, layers=layers_to_process)
        for layer in layers_to_process:
            if not (feats := decoded.get(layer)):
                continue
            
            gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs=settings.default_crs)
            gdf = validate_geometries(gdf)
            if gdf.empty:
                logger.debug("No valid geometries for layer '%s' in tile %d/%d/%d", layer, z,x,y)
                continue
            
            tmp_out = settings.temp_dir / f"{layer}_{z}_{x}_{y}.geojson"
            gdf.to_file(tmp_out, driver="GeoJSON")
            layer_temp_files[layer].append(tmp_out)
    
    # 4. Stitch and Persist per layer
    stitcher = GeometryStitcher(target_crs=settings.default_crs)
    persister = PostGISPersister(str(settings.database_url))
    if recreate_db:
        logger.info("Recreating database: %s", settings.database_url.path)
        persister.recreate_database()

    for layer, files in layer_temp_files.items():
        if not files:
            logger.warning("Layer '%s': No temporary files found to stitch, skipping.", layer)
            continue
        
        try:
            gdfs = [gpd.read_file(f, crs=settings.default_crs) for f in files]
        except Exception as e:
            logger.error("Failed to read GeoJSON files for layer '%s': %s", layer, e)
            continue

        id_col = settings.id_column_per_layer.get(layer)
        agg_rules = settings.aggregation_rules_per_layer.get(layer, {})

        logger.info(
            "Stitching layer '%s' using ID column '%s' and %d aggregation rules.",
            layer, id_col, len(agg_rules)
        )
        
        stitched_gdf = stitcher.stitch_geometries(
            gdfs, layer_name=layer, id_column=id_col, agg_rules=agg_rules
        )

        if stitched_gdf.empty:
            logger.warning("Stitching layer '%s' resulted in an empty GeoDataFrame. Skipping.", layer)
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
        persister.write(stitched_gdf, table=table_name)

    logger.info("🎉 Pipeline finished successfully. 🎉")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Suhail.AI MVT Processing Pipeline")
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("W", "S", "E", "N"),
        help="Bounding box (W S E N) in EPSG:4326 coordinates.",
    )
    parser.add_argument(
        "--zoom",
        type=int,
        default=15,
        help="Zoom level to download tiles for.",
    )
    parser.add_argument(
        "--layers",
        type=str,
        help="Optional comma-separated list of layers to process, overriding config.",
    )
    parser.add_argument(
        "--recreate-db",
        action="store_true",
        help="Drop and recreate the target database before writing data.",
    )
    args = parser.parse_args()

    layer_list_override = args.layers.split(",") if args.layers else None

    asyncio.run(
        run_pipeline(
            aoi_bbox=tuple(args.bbox),
            zoom=args.zoom,
            layers_override=layer_list_override,
            recreate_db=args.recreate_db,
        )
    ) 