from __future__ import annotations

import asyncio
import logging
from typing import Dict, List, Tuple, Optional

import aiohttp
import geopandas as gpd
import pandas as pd
import typer
from sqlalchemy.orm import Session
from sqlalchemy import inspect

from meshic_pipeline.config import settings
from meshic_pipeline.persistence.db import get_db_engine
from meshic_pipeline.persistence.models import TileURL
from meshic_pipeline.decoder.mvt_decoder import MVTDecoder
from meshic_pipeline.geometry.validator import validate_geometries
from meshic_pipeline.persistence.postgis_persister import (
    PostGISPersister,
    SCHEMA_MAP,
    ensure_neighborhood_centroids_primary_key,
    ensure_neighborhood_stubs_for_parcels,
    ensure_subdivision_stubs_for_parcels,
)
from meshic_pipeline.persistence.table_management import reset_temp_table
from meshic_pipeline.pipeline_orchestrator import decode_and_validate_tile


logger = logging.getLogger(__name__)
app = typer.Typer()


async def fetch_many(urls: List[str], concurrency: int = 20, delay: float = 0.05, retries: int = 2) -> Dict[str, tuple[bytes | None, str | None]]:
    semaphore = asyncio.Semaphore(concurrency)

    async def _get(client: aiohttp.ClientSession, url: str) -> Tuple[str, bytes | None, str | None]:
        async with semaphore:
            attempt = 0
            last_error: str | None = None
            while True:
                try:
                    async with client.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            return url, data, None
                        # Retry only on transient statuses
                        if resp.status in {408, 425, 429, 500, 502, 503, 504} and attempt < retries:
                            attempt += 1
                            last_error = f"HTTP {resp.status}"
                            await asyncio.sleep(min(1.0 * attempt, 3.0))
                            continue
                        logger.warning("Tile fetch failed %s: HTTP %s", url, resp.status)
                        return url, None, f"HTTP {resp.status}"
                except Exception as e:
                    logger.error("Tile fetch exception %s: %s", url, e)
                    if attempt < retries:
                        attempt += 1
                        last_error = f"exception: {e}"
                        await asyncio.sleep(min(1.0 * attempt, 3.0))
                        continue
                    return url, None, f"exception: {e}"

    connector = aiohttp.TCPConnector(limit=concurrency)
    timeout = aiohttp.ClientTimeout(total=60)
    results: Dict[str, tuple[bytes | None, str | None]] = {}
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as client:
        tasks = [_get(client, u) for u in urls]
        for coro in asyncio.as_completed(tasks):
            url, data, err = await coro
            results[url] = (data, err)
            if delay:
                await asyncio.sleep(delay)
    return results


def _url_to_coords(url: str) -> Tuple[int, int, int]:
    parts = url.strip().split("/")
    # .../maps/<region>/<z>/<x>/<y>.vector.pbf
    z = int(parts[-3])
    x = int(parts[-2])
    y = int(parts[-1].split(".")[0])
    return z, x, y


def _apply_arabic_and_columns(layer_name: str, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = MVTDecoder.apply_arabic_column_mapping(gdf)
    if layer_name == "neighborhoods-centroids":
        gdf = ensure_neighborhood_centroids_primary_key(gdf)
    allowed_cols = set(SCHEMA_MAP.get(layer_name, {}).keys())
    if "geometry" in gdf.columns:
        allowed_cols.add("geometry")
    return gdf[[c for c in gdf.columns if c in allowed_cols]]


def enrich_parcels_with_spatial_assignments(gdf: gpd.GeoDataFrame, persister: PostGISPersister) -> gpd.GeoDataFrame:
    """
    🔧 FIX: Add spatial assignments for neighborhood_id and province_id to parcels.
    This function addresses the missing spatial join logic that caused 1M+ parcels to be unassigned.
    """
    if gdf.empty:
        return gdf
    
    logger.info("🔗 Enriching %d parcels with spatial assignments...", len(gdf))
    
    # Create temporary table for spatial joins
    import uuid
    temp_table = f"temp_parcels_enrich_{uuid.uuid4().hex[:12]}"
    
    try:
        # Write parcels to temp table
        persister.write(gdf, "parcels", temp_table, if_exists="replace", id_column=None)
        
        # Create spatial index for performance
        persister.execute(f'CREATE INDEX IF NOT EXISTS idx_{temp_table}_geom ON "{temp_table}" USING GIST("geometry")')
        
        # Step 1: Assign neighborhood_id via spatial join
        logger.info("📍 Step 1: Assigning neighborhood_id via spatial intersection...")
        
        # First, add the columns if they don't exist
        persister.execute(f'ALTER TABLE "{temp_table}" ADD COLUMN IF NOT EXISTS neighborhood_id BIGINT;')
        persister.execute(f'ALTER TABLE "{temp_table}" ADD COLUMN IF NOT EXISTS province_id BIGINT;')
        persister.execute(f'ALTER TABLE "{temp_table}" ADD COLUMN IF NOT EXISTS neighborhood_ar VARCHAR;')
        
        update_neighborhood_sql = f"""
            UPDATE "{temp_table}" AS p
            SET neighborhood_id = n.neighborhood_id,
                neighborhood_ar = COALESCE(p.neighborhood_ar, n.neighborhood_ar)
            FROM neighborhoods n
            WHERE ST_Intersects(p.geometry, n.geometry)
            AND p.neighborhood_id IS NULL;
        """
        persister.execute(update_neighborhood_sql)
        
        # Step 2: Assign province_id via neighborhood inheritance
        logger.info("🏛️ Step 2: Assigning province_id via neighborhood inheritance...")
        update_province_sql = f"""
            UPDATE "{temp_table}" AS p
            SET province_id = n.province_id
            FROM neighborhoods n
            WHERE p.neighborhood_id = n.neighborhood_id
            AND p.province_id IS NULL
            AND n.province_id IS NOT NULL;
        """
        persister.execute(update_province_sql)
        
        # Step 3: Fallback province assignment via geographical bounding boxes
        logger.info("🗺️ Step 3: Fallback province assignment via geographical coordinates...")
        
        # Use actual database bounding boxes instead of hardcoded approximations
        fallback_sql = f"""
            UPDATE "{temp_table}" AS p
            SET province_id = prov.province_id
            FROM provinces prov
            WHERE p.province_id IS NULL
            AND prov.bbox_sw_lon IS NOT NULL
            AND ST_X(ST_Centroid(p.geometry)) BETWEEN prov.bbox_sw_lon AND prov.bbox_ne_lon
            AND ST_Y(ST_Centroid(p.geometry)) BETWEEN prov.bbox_sw_lat AND prov.bbox_ne_lat;
        """
        persister.execute(fallback_sql)
        
        # Read back enriched data
        enriched_gdf = persister.read_sql(f'SELECT * FROM "{temp_table}"')
        
        # Log assignment statistics
        total_parcels = len(enriched_gdf)
        with_neighborhood = len(enriched_gdf[enriched_gdf['neighborhood_id'].notna()])
        with_province = len(enriched_gdf[enriched_gdf['province_id'].notna()])
        
        logger.info("✅ Spatial assignment complete:")
        logger.info("   • Total parcels: %d", total_parcels)
        logger.info("   • With neighborhood_id: %d (%.1f%%)", with_neighborhood, with_neighborhood/total_parcels*100)
        logger.info("   • With province_id: %d (%.1f%%)", with_province, with_province/total_parcels*100)
        
        return enriched_gdf
        
    except Exception as e:
        logger.error("❌ Spatial assignment failed: %s", e)
        return gdf
    finally:
        # Cleanup temp table
        try:
            persister.drop_table(temp_table)
        except:
            pass


class AdaptiveConcurrency:
    def __init__(self, initial: int = 5, min_val: int = 2, max_val: int = 20):
        self.current = initial
        self.min_val = min_val
        self.max_val = max_val
        self.success_window = []
        self.window_size = 100
        self.adjustment_threshold = 50
        
    def record_batch(self, success_count: int, total_count: int):
        success_rate = success_count / max(total_count, 1)
        self.success_window.append(success_rate)
        if len(self.success_window) > self.window_size:
            self.success_window.pop(0)
            
        if len(self.success_window) >= self.adjustment_threshold:
            avg_success = sum(self.success_window) / len(self.success_window)
            if avg_success > 0.95 and self.current < self.max_val:
                self.current = min(self.current + 2, self.max_val)
                logger.info(f"Increased concurrency to {self.current} (success rate: {avg_success:.3f})")
            elif avg_success < 0.85 and self.current > self.min_val:
                self.current = max(self.current - 1, self.min_val)
                logger.info(f"Decreased concurrency to {self.current} (success rate: {avg_success:.3f})")

@app.command()
def main(
    batch_size: int = typer.Option(1000, "--batch-size", help="Tiles to claim per batch"),
    concurrency: int = typer.Option(5, "--concurrency", help="Initial concurrent HTTP requests (adaptive)"),
    delay: float = typer.Option(0.05, "--request-delay", help="Delay between requests (s)"),
    recreate_db: bool = typer.Option(False, "--recreate-db", help="Drop and recreate database schema"),
    save_as_temp: Optional[str] = typer.Option(None, "--save-as-temp", help="Save parcels to a temp table"),
    max_retries: int = typer.Option(5, "--max-retries", help="Max retries before permanent failure"),
    adaptive: bool = typer.Option(True, "--adaptive/--no-adaptive", help="Enable adaptive concurrency"),
    enable_spatial_assignment: bool = typer.Option(True, "--spatial/--no-spatial", help="Enable spatial assignment of province_id"),
):
    """Run geometric pipeline in DB-driven mode using the tile_urls queue with FIXED spatial assignment logic."""
    
    if enable_spatial_assignment:
        logger.info("🔧 RUNNING WITH FIXED SPATIAL ASSIGNMENT LOGIC")
    else:
        logger.warning("⚠️ Running without spatial assignment - parcels will not get province_id!")
    
    engine = get_db_engine(str(settings.database_url))
    session = Session(engine)

    # Reset stale
    TileURL.reset_stale_in_progress(session, stale_minutes=60)

    persister = PostGISPersister(str(settings.database_url))
    if recreate_db:
        persister.recreate_database()

    inspector = inspect(persister.engine)
    adaptive_controller = AdaptiveConcurrency(initial=concurrency) if adaptive else None
    current_concurrency = concurrency

    while True:
        tiles = TileURL.claim_tiles_for_processing(session, batch_size=batch_size, max_retries=max_retries)
        if not tiles:
            typer.echo("No more pending/failed tiles. Exiting.")
            break

        urls = [t.url for t in tiles]
        fetch_map = asyncio.run(fetch_many(urls, concurrency=current_concurrency, delay=delay, retries=2))
        
        # Count successes for adaptive control
        successes = sum(1 for url in urls if fetch_map.get(url, (None, None))[0] is not None)
        if adaptive_controller:
            adaptive_controller.record_batch(successes, len(urls))
            current_concurrency = adaptive_controller.current

        layer_to_gdfs: Dict[str, List[gpd.GeoDataFrame]] = {}
        urls_decode_ok: List[str] = []
        for t in tiles:
            data, err = fetch_map.get(t.url, (None, None))
            if not data:
                TileURL.update_status(session, t.url, "failed", error_message=(err or "fetch_failed"))
                continue
            try:
                z, x, y = _url_to_coords(t.url)
                decoded = decode_and_validate_tile((z, x, y), data, settings.layers_to_process, settings.default_crs)
                for layer_name, gdf in decoded:
                    if gdf is None or gdf.empty:
                        continue
                    gdf = _apply_arabic_and_columns(layer_name, gdf)
                    if not gdf.empty:
                        layer_to_gdfs.setdefault(layer_name, []).append(gdf)
                urls_decode_ok.append(t.url)
            except Exception as e:
                TileURL.update_status(session, t.url, "failed", error_message=str(e))

        def persist_layers() -> None:
            for layer in settings.layers_to_process:
                gdfs = layer_to_gdfs.get(layer)
                if not gdfs:
                    continue

                table_name = settings.table_name_mapping.get(layer, layer)
                if not inspector.has_table(table_name, schema="public"):
                    logger.warning("Skipping layer '%s': target table '%s' missing", layer, table_name)
                    continue

                temp_table = f"temp_{table_name}"
                reset_temp_table(persister.engine, table_name, temp_table)

                gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

                pk_col = settings.id_column_per_layer.get(layer)
                if pk_col and pk_col in gdf.columns:
                    before = len(gdf)
                    gdf = gdf[gdf[pk_col].notna()]
                    dropped = before - len(gdf)
                    if dropped:
                        logger.warning(
                            "Dropped %d row(s) with null %s for layer '%s' before persist",
                            dropped,
                            pk_col,
                            layer,
                        )
                    gdf = gdf.drop_duplicates(subset=[pk_col])

                if layer == "parcels" and enable_spatial_assignment:
                    gdf = enrich_parcels_with_spatial_assignments(gdf, persister)

                persister.write(
                    gdf,
                    layer,
                    temp_table,
                    if_exists="replace",
                    id_column=None,
                    chunksize=settings.db_chunk_size,
                )

                if layer == "parcels" and save_as_temp:
                    persister.write(
                        gdf,
                        layer,
                        save_as_temp,
                        if_exists="replace",
                        id_column=None,
                        chunksize=settings.db_chunk_size,
                    )
                else:
                    table_name = settings.table_name_mapping.get(layer, layer)
                    id_col = settings.id_column_per_layer.get(layer)

                    if layer in ("neighborhoods", "parcels", "subdivisions") and "province_id" in gdf.columns:
                        try:
                            existing_df = pd.read_sql("SELECT province_id FROM provinces", persister.engine)
                            existing = set(existing_df["province_id"]) if not existing_df.empty else set()
                            incoming = {int(x) for x in gdf["province_id"].dropna().unique()}
                            missing = incoming - existing
                            if missing:
                                to_insert_data = []
                                for pid in missing:
                                    province_name = f"Unknown_{pid}"
                                    province_name_ar = f"غير محدد_{pid}"
                                    spid = str(pid)
                                    if spid.startswith("101"):
                                        province_name_ar = f"الرياض_منطقة_{pid}"
                                        province_name = f"Riyadh_Region_{pid}"
                                    elif spid.startswith("21"):
                                        province_name_ar = f"مكة_منطقة_{pid}"
                                        province_name = f"Makkah_Region_{pid}"
                                    elif spid.startswith("51"):
                                        province_name_ar = f"الشرقية_منطقة_{pid}"
                                        province_name = f"Eastern_Region_{pid}"
                                    elif spid.startswith("131"):
                                        province_name_ar = f"المدينة_منطقة_{pid}"
                                        province_name = f"Madinah_Region_{pid}"
                                    to_insert_data.append(
                                        {
                                            "province_id": pid,
                                            "province_name": province_name,
                                            "province_name_ar": province_name_ar,
                                        }
                                    )
                                to_insert_df = pd.DataFrame(to_insert_data)
                                to_insert_df.to_sql(
                                    "provinces", persister.engine, if_exists="append", index=False, method="multi"
                                )
                                logger.info(
                                    "Inserted %d missing province stub(s) prior to %s upsert",
                                    len(to_insert_data),
                                    layer,
                                )
                        except Exception as e:
                            logger.warning("Could not pre-insert provinces for %s: %s", layer, e)

                    if layer == "parcels":
                        ensure_neighborhood_stubs_for_parcels(gdf, persister.engine)
                        ensure_subdivision_stubs_for_parcels(gdf, persister.engine)

                    if layer == "parcels" and "ruleid" in gdf.columns:
                        try:
                            existing_df = pd.read_sql("SELECT ruleid FROM zoning_rules", persister.engine)
                            existing = set(existing_df["ruleid"]) if not existing_df.empty else set()
                            incoming = set(gdf["ruleid"].dropna().unique())
                            missing = incoming - existing
                            if missing:
                                to_insert = (
                                    gdf[gdf["ruleid"].isin(missing)][["ruleid"]].drop_duplicates("ruleid")
                                )
                                to_insert.to_sql(
                                    "zoning_rules", persister.engine, if_exists="append", index=False, method="multi"
                                )
                                logger.info(
                                    "Inserted %d missing zoning rule(s) prior to parcel upsert", len(to_insert)
                                )
                        except Exception as e:
                            logger.warning("Could not pre-insert zoning_rules for parcels: %s", e)

                    if id_col:
                        persister.write(
                            gdf,
                            layer,
                            table_name,
                            id_column=id_col,
                            chunksize=settings.db_chunk_size,
                        )
                    else:
                        persister.write(
                            gdf,
                            layer,
                            table_name,
                            if_exists="replace",
                            id_column=None,
                            chunksize=settings.db_chunk_size,
                        )

        try:
            persist_layers()
        except Exception as e:
            logger.exception(
                "Batch persist failed; re-queuing %d decoded tile URL(s) for retry",
                len(urls_decode_ok),
            )
            msg = (str(e) or type(e).__name__)[:400]
            for u in urls_decode_ok:
                TileURL.update_status(session, u, "pending", error_message=f"persist_failed: {msg}")
            continue

        for u in urls_decode_ok:
            TileURL.update_status(session, u, "processed")

    session.close()


if __name__ == "__main__":
    app()
