from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List

import geopandas as gpd

from .config import AppConfig
from .discovery.tile_endpoint_discovery import get_tile_coordinates_for_bounds
from .downloader.async_tile_downloader import AsyncTileDownloader
from .decoder.mvt_decoder import MVTDecoder
from .geometry.validator import validate_geometries
from .geometry.stitcher import GeometryStitcher
from .persistence.postgis_persister import PostGISPersister

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("orchestrator")


async def run_pipeline(config: AppConfig, recreate_db: bool = False) -> None:
    config.ensure_dirs()

    # ------------------------------------------------------------------
    # 1. Discover tiles --------------------------------------------------
    # ------------------------------------------------------------------
    tiles = get_tile_coordinates_for_bounds(config.aoi_bbox, config.zoom)
    logger.info("Need %d tiles at z%d", len(tiles), config.zoom)

    # ------------------------------------------------------------------
    # 2. Download tiles --------------------------------------------------
    # ------------------------------------------------------------------
    async with AsyncTileDownloader(config.cache_dir, config.max_concurrent) as dl:
        raw_tiles = await dl.download_many(tiles)

    # ------------------------------------------------------------------
    # 3. Decode and write temp GeoJSONs ---------------------------------
    # ------------------------------------------------------------------
    decoder = MVTDecoder()
    layer_temp_files: Dict[str, List[Path]] = {layer: [] for layer in config.layers}

    for (z, x, y), data in raw_tiles.items():
        decoded = decoder.decode_bytes(data, z=z, x=x, y=y, layers=config.layers)
        for layer in config.layers:
            feats = decoded.get(layer)
            if not feats:
                continue
            gdf = gpd.GeoDataFrame(feats, geometry="geometry", crs="EPSG:4326")
            gdf = validate_geometries(gdf)
            tmp_out = config.temp_dir / f"{layer}_{z}_{x}_{y}.geojson"
            gdf.to_file(tmp_out, driver="GeoJSON")
            layer_temp_files[layer].append(tmp_out)

    # ------------------------------------------------------------------
    # 4. Stitch per layer ----------------------------------------------
    # ------------------------------------------------------------------
    stitcher = GeometryStitcher()
    persister = PostGISPersister(config.database_url)
    if recreate_db:
        persister.recreate_database()

    for layer, files in layer_temp_files.items():
        if not files:
            logger.warning("Layer %s: no features found, skipping", layer)
            continue
        gdfs = [gpd.read_file(f) for f in files]
        # Heuristic id column
        id_col = next((c for c in gdfs[0].columns if c.endswith("_id") or c == "strip_id"), None)
        if id_col is None and "name" in gdfs[0].columns:
            id_col = "name"
        stitched = stitcher.stitch_geometries(gdfs, id_col)
        out_path = config.stitched_dir / f"{layer}_stitched.geojson"
        stitched.to_file(out_path, driver="GeoJSON")
        logger.info("Wrote stitched layer %s → %s (%d features)", layer, out_path, len(stitched))
        persister.write(stitched, table=layer)

    logger.info("Pipeline finished successfully.")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Suhail tile pipeline")
    parser.add_argument("--bbox", nargs=4, type=float, required=True, metavar=("W", "S", "E", "N"))
    parser.add_argument("--zoom", type=int, default=15)
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--layers", type=str, help="Comma separated layer list (optional)")
    parser.add_argument("--recreate-db", action="store_true", help="Drop and recreate database before writing")
    args = parser.parse_args()

    if args.layers:
        layer_list = tuple(args.layers.split(","))
    else:
        # default from schema without creating instance
        layer_list = AppConfig.model_fields["layers"].default  # type: ignore

    cfg = AppConfig(
        database_url=args.database_url,
        aoi_bbox=tuple(args.bbox),
        zoom=args.zoom,
        layers=layer_list,
    )

    asyncio.run(run_pipeline(cfg, recreate_db=args.recreate_db)) 