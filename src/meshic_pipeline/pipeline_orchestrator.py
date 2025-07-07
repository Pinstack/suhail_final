from __future__ import annotations

import logging
from typing import Dict, List, Tuple
import uuid
import concurrent.futures

import geopandas as gpd
import sys
from tqdm import tqdm
import pandas as pd
from sqlalchemy import create_engine, inspect

from .config import settings
from .discovery.tile_endpoint_discovery import (
    get_tile_coordinates_for_bounds,
    get_tile_coordinates_for_grid,
)
from .utils.tile_list_generator import tiles_from_bbox_z
from .downloader.async_tile_downloader import AsyncTileDownloader
from .decoder.mvt_decoder import MVTDecoder
from .geometry.validator import validate_geometries
from .geometry.stitcher import GeometryStitcher
from .memory_utils import memory_optimized, get_memory_monitor
from .persistence.postgis_persister import PostGISPersister, SCHEMA_MAP
from sqlalchemy import text
from meshic_pipeline.persistence.table_management import reset_temp_table


def setup_logging():
    """Configure logging based on settings."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_level = (
        settings.log_level.value
        if hasattr(settings.log_level, "value")
        else settings.log_level
    )

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
        file_handler = logging.FileHandler(settings.log_file, mode="a")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(file_handler)

    # Set the level for the root logger
    root_logger.setLevel(log_level)


setup_logging()
logger = logging.getLogger(__name__)


def enrich_parcels_with_region_id(
    gdf: gpd.GeoDataFrame, persister: PostGISPersister
) -> gpd.GeoDataFrame:
    """Enrich parcels GeoDataFrame with region_id using PostGIS."""

    temp_table = f"temp_parcels_enrich_{uuid.uuid4().hex[:8]}"
    gdf_to_write = gdf.copy()
    if "region_id" not in gdf_to_write.columns:
        gdf_to_write["region_id"] = None

    # Persist to a temporary table
    persister.write(
        gdf_to_write, "parcels", temp_table, if_exists="replace", id_column=None
    )

    # Ensure spatial indexes for efficient join
    persister.execute(
        f'CREATE INDEX IF NOT EXISTS idx_{temp_table}_geom ON public."{temp_table}" USING GIST("geometry")'
    )
    persister.execute(
        'CREATE INDEX IF NOT EXISTS idx_neighborhoods_geometry ON public.neighborhoods USING GIST("geometry")'
    )

    update_sql = f"""
        UPDATE public."{temp_table}" AS p
        SET region_id = n.region_id
        FROM neighborhoods n
        WHERE ST_Intersects(p.geometry, n.geometry);
    """
    persister.execute(update_sql)

    enriched = persister.read_sql(f'SELECT * FROM "{temp_table}"')
    persister.drop_table(temp_table)
    return enriched


@memory_optimized()
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

    monitor = get_memory_monitor()
    logger.debug(
        "Memory before decoding tile %s/%s/%s: %.2fMB",
        z,
        x,
        y,
        monitor.get_memory_stats().process_mb,
    )

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

    stats = monitor.get_memory_stats()
    logger.debug(
        "Memory after decoding tile %s/%s/%s: %.2fMB",
        z,
        x,
        y,
        stats.process_mb,
    )
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
    monitor = get_memory_monitor()
    start_mem = monitor.get_memory_stats().process_mb
    overall_start_mem = start_mem

    logger.info(
        "Starting pipeline run for AOI: %s at zoom %d",
        aoi_bbox or province or "grid",
        zoom,
    )
    logger.debug("Using settings: %s", settings.model_dump_json(indent=2))

    # Tile discovery based on province metadata
    if saudi_arabia_mode:
        tiles = []
        for prov_key in settings.list_provinces():
            meta = settings.get_province_meta(prov_key)
            tiles.extend(tiles_from_bbox_z(meta["bbox_z15"], zoom=15))
        logger.info(
            "🇸🇦 Saudi Arabia mode: Discovered %d tiles across all provinces",
            len(tiles),
        )
    elif province:
        meta = settings.get_province_meta(province)
        tiles = tiles_from_bbox_z(meta["bbox_z15"], zoom=15)
        logger.info(
            "🏛️ Province mode (%s): Discovered %d tiles",
            province,
            len(tiles),
        )
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
        logger.info(
            "🔢 Grid mode: Discovered %d tiles for %dx%d grid",
            len(tiles),
            settings.grid_w,
            settings.grid_h,
        )

    # 2. Determine tile server URL
    if province:
        tile_base_url = settings.get_province_meta(province)["tile_url_template"].split("/{z}")[0]
    elif saudi_arabia_mode:
        # Use first province URL; all provinces currently share same domain pattern
        first_meta = settings.get_province_meta(settings.list_provinces()[0])
        tile_base_url = first_meta["tile_url_template"].split("/{z}")[0]
    else:
        tile_base_url = settings.tile_base_url
    logger.info("🌐 Using tile server: %s", tile_base_url)

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

    for layer in tqdm(layers_to_process, desc="Processing Layers"):
        logger.info("--- Starting processing for layer: %s ---", layer)
        temp_table = f"temp_{layer}"
        prod_table = layer  # Assumes production table name matches layer name
        # Check if production table exists; skip if not
        inspector = inspect(persister.engine)
        if not inspector.has_table(prod_table, schema="public"):
            logger.warning(f"Skipping layer '{layer}': production table '{prod_table}' does not exist.")
            continue
        reset_temp_table(persister.engine, prod_table, temp_table)

        # Collect all decoded features for each layer
        layer_gdfs = {}
        for (z, x, y), data in non_empty_tiles.items():
            decoded_layers = decode_and_validate_tile((z, x, y), data, [layer], settings.default_crs)
            for _layer_name, gdf in decoded_layers:
                gdf = MVTDecoder.apply_arabic_column_mapping(gdf)
                # Filter columns to only those in the canonical schema for this layer
                allowed_cols = set(SCHEMA_MAP.get(_layer_name, {}).keys())
                # Always keep geometry column
                if 'geometry' in gdf.columns:
                    allowed_cols.add('geometry')
                gdf = gdf[[col for col in gdf.columns if col in allowed_cols]]
                if not gdf.empty:
                    if _layer_name not in layer_gdfs:
                        layer_gdfs[_layer_name] = [gdf]
                    else:
                        layer_gdfs[_layer_name].append(gdf)

        for layer, gdf_list in layer_gdfs.items():
            gdf = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True))
            # Deduplicate by primary key if applicable (DRY for all layers)
            pk_col = settings.id_column_per_layer.get(layer)
            if pk_col and pk_col in gdf.columns:
                before = len(gdf)
                gdf = gdf.drop_duplicates(subset=[pk_col])
                after = len(gdf)
                if after < before:
                    logger.warning(f"Dropped {before - after} duplicate rows for primary key '{pk_col}' in layer '{layer}' before DB write.")
            # --- Audit for unseen ruleid values before DB write (parcels only) ---
            if layer == 'parcels' and 'ruleid' in gdf.columns:
                engine = persister.engine
                zoning_rules = pd.read_sql('SELECT ruleid FROM zoning_rules', engine)
                incoming_ruleids = set(gdf['ruleid'].dropna().unique())
                existing_ruleids = set(zoning_rules['ruleid'])
                missing_ruleids = incoming_ruleids - existing_ruleids
                if missing_ruleids:
                    print(f"[WARNING] Missing ruleid values in zoning_rules: {missing_ruleids}")
                    # --- Enhanced auto-insert: include zoning_id, zoning_color, zoning_group if present ---
                    insert_cols = ['ruleid']
                    for col in ['zoning_id', 'zoning_color', 'zoning_group']:
                        if col in gdf.columns:
                            insert_cols.append(col)
                    to_insert = gdf[gdf['ruleid'].isin(missing_ruleids)][insert_cols].drop_duplicates('ruleid')
                    # Fill missing columns with None if not present
                    for col in ['zoning_id', 'zoning_color', 'zoning_group']:
                        if col not in to_insert.columns:
                            to_insert[col] = None
                    to_insert.to_sql('zoning_rules', engine, if_exists='append', index=False, method='multi')
                    print(f"[INFO] Inserted {len(to_insert)} new ruleid(s) into zoning_rules with available zoning metadata.")
                else:
                    print("[INFO] All ruleid values present in zoning_rules.")
            # Write to DB in a single operation
            persister.write(
                gdf,
                layer,
                temp_table,
                if_exists="replace",
                id_column=None,
            )

        # --- Enrichment Step: Assign region_id to parcels ---
        if layer == "parcels":
            logger.info("Enriching parcels with region_id via spatial join...")
            # Load neighborhoods from DB
            neighborhoods = gpd.read_postgis(
                "SELECT neighborhood_id, region_id, geometry FROM neighborhoods",
                persister.engine,
                geom_col="geometry",
            )
            # Spatial join for region_id
            parcels_enriched = gpd.sjoin(
                gpd.read_postgis(
                    f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
                ),
                neighborhoods[["region_id", "geometry"]],
                how="left",
                predicate="intersects",
            )
            persister.write(
                parcels_enriched,
                "parcels_enriched",
                "parcels_enriched",
                if_exists="replace",
                id_column=None,
                chunksize=settings.db_chunk_size,
            )
            logger.info("Enrichment complete: region_id assigned where possible.")

        # Save stitched file locally
        out_path = settings.stitched_dir / f"{layer}_stitched.geojson"
        gpd.read_postgis(
            f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
        ).to_file(out_path, driver="GeoJSON")

        # Persist to PostGIS
        if layer == "parcels" and save_as_temp:
            logger.info(
                "Writing parcels to temp table %s for delta comparison", save_as_temp
            )
            persister.write(
                gpd.read_postgis(
                    f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
                ),
                layer,
                save_as_temp,
                if_exists="replace",
                id_column=None,
                chunksize=settings.db_chunk_size,
            )
            persister.execute(
                f'CREATE INDEX IF NOT EXISTS idx_{save_as_temp}_id ON public."{save_as_temp}" (parcel_objectid)'
            )
            persister.execute(
                f'CREATE INDEX IF NOT EXISTS idx_{save_as_temp}_geom ON public."{save_as_temp}" USING GIST("geometry")'
            )
        else:
            table_name = settings.table_name_mapping.get(layer, layer)
            logger.info(
                "Persisting %d features for layer '%s' to table '%s'",
                len(gpd.read_postgis(
                    f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
                )),
                layer,
                table_name,
            )

            # Determine write mode: upsert if id_col is set, else replace (see WHAT_TO_DO_NEXT_PIPELINE_TABLES.md)
            id_col = settings.id_column_per_layer.get(layer)
            if id_col:
                persister.write(
                    gpd.read_postgis(
                        f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
                    ),
                    layer,
                    table_name,
                    id_column=id_col,
                    chunksize=settings.db_chunk_size,
                )
            else:
                persister.write(
                    gpd.read_postgis(
                        f'SELECT * FROM "{temp_table}"', persister.engine, geom_col="geometry"
                    ),
                    layer,
                    table_name,
                    if_exists="replace",
                    id_column=None,
                    chunksize=settings.db_chunk_size,
                )
        logger.info("--- Finished processing for layer: %s ---", layer)
        layer_mem = monitor.get_memory_stats().process_mb
        logger.info(
            "Memory delta for layer '%s': %.2fMB",
            layer,
            layer_mem - start_mem,
        )
        start_mem = layer_mem

    final_mem = monitor.get_memory_stats().process_mb
    logger.info("🎉 Pipeline finished successfully. 🎉")
    logger.info(
        "Total memory change during run: %.2fMB",
        final_mem - overall_start_mem,
    )
