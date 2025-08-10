import typer
import subprocess
import sys
from typing import List, Optional
from pathlib import Path
from meshic_pipeline import run_enrichment_pipeline

# Determine the directory containing this CLI file
SCRIPT_DIR = Path(__file__).parent

app = typer.Typer(help="Unified CLI for the Suhail pipeline")

@app.command()
def geometric(
    bbox: Optional[List[float]] = typer.Option(
        None,
        "--bbox",
        "-b",
        help="Bounding box: min_lon min_lat max_lon max_lat"
    ),
    recreate_db: bool = typer.Option(
        False,
        "--recreate-db",
        help="Drop and recreate the database schema."
    ),
    save_as_temp: Optional[str] = typer.Option(
        None,
        "--save-as-temp",
        help="Save parcels to a temporary table with this name."
    ),
):
    """Run the geometric pipeline (Stage 1)."""
    script = SCRIPT_DIR / "run_geometric_pipeline.py"
    cmd = [sys.executable, str(script)]
    if bbox:
        cmd += ["--bbox"] + [str(x) for x in bbox]
    if recreate_db:
        cmd.append("--recreate-db")
    if save_as_temp:
        cmd += ["--save-as-temp", save_as_temp]
    subprocess.run(cmd, check=True)

@app.command()
def fast_enrich(
    batch_size: int = typer.Option(200, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich new parcels that have transaction prices but haven't been enriched yet."""
    run_enrichment_pipeline.fast_enrich(batch_size=batch_size, limit=limit)

@app.command()
def incremental_enrich(
    batch_size: int = typer.Option(100, "--batch-size", help="Number of parcels per batch"),
    days_old: int = typer.Option(30, "--days-old", help="Days old threshold for stale data"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich parcels that haven't been updated in the specified number of days."""
    run_enrichment_pipeline.incremental_enrich(batch_size=batch_size, days_old=days_old, limit=limit)

@app.command()
def full_refresh(
    batch_size: int = typer.Option(50, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich ALL parcels with transaction prices (complete refresh)."""
    run_enrichment_pipeline.full_refresh(batch_size=batch_size, limit=limit)

@app.command()
def universal_metrics(
    batch_size: int = typer.Option(200, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich ALL parcels with derived price metrics (including those without transaction data)."""
    run_enrichment_pipeline.universal_metrics(batch_size=batch_size, limit=limit)

@app.command()
def delta_enrich(
    batch_size: int = typer.Option(200, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
    fresh_table: str = typer.Option("parcels_fresh_mvt", "--fresh-table", help="Fresh MVT table name"),
    auto_geometric: bool = typer.Option(False, "--auto-geometric", help="Auto-run geometric pipeline first"),
    show_details: bool = typer.Option(True, "--show-details/--no-details", help="Show change analysis"),
):
    """🎯 Delta enrichment: Only process parcels with actual transaction price changes (most efficient)."""
    run_enrichment_pipeline.delta_enrich(batch_size=batch_size, limit=limit, fresh_mvt_table=fresh_table, auto_run_geometric=auto_geometric, show_details=show_details)

@app.command()
def smart_pipeline(
    geometric_first: bool = typer.Option(True, "--geometric-first", help="Run geometric pipeline first"),
    batch_size: int = typer.Option(300, "--batch-size", help="Enrichment batch size"),
    bbox: Optional[List[float]] = typer.Option(None, "--bbox", help="Bounding box: W S E N"),
):
    """🧠 Smart pipeline: Complete geometric + enrichment workflow (recommended for full runs)."""
    script = SCRIPT_DIR / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "smart-pipeline-enrich", "--batch-size", str(batch_size)]
    if not geometric_first:
        cmd += ["--no-geometric-first"]
    if bbox and len(bbox) == 4:
        cmd += ["--bbox"] + [str(x) for x in bbox]
    subprocess.run(cmd, check=True)

@app.command()
def monitor(
    action: str = typer.Argument(
        ..., help="Monitoring action: status, recommend, schedule-info"
    ),
):
    """Run enrichment monitoring commands."""
    script = SCRIPT_DIR / "run_monitoring.py"
    cmd = [sys.executable, str(script), action]
    subprocess.run(cmd, check=True)

@app.command()
def province_geometric(
    province: str = typer.Argument(..., help="Province name: al_qassim, riyadh, madinah, asir, eastern, makkah"),
    strategy: str = typer.Option("optimal", "--strategy", "-s", help="Discovery strategy: optimal, efficient, comprehensive"),
    recreate_db: bool = typer.Option(False, "--recreate-db", help="Drop and recreate the database schema"),
    save_as_temp: Optional[str] = typer.Option(None, "--save-as-temp", help="Save parcels to a temporary table"),
):
    """🏛️ Run geometric pipeline for a specific Saudi province using enhanced discovery."""
    script = SCRIPT_DIR / "run_geometric_pipeline.py"
    cmd = [sys.executable, str(script), "--province", province, "--strategy", strategy]
    if recreate_db:
        cmd.append("--recreate-db")
    if save_as_temp:
        cmd += ["--save-as-temp", save_as_temp]
    subprocess.run(cmd, check=True)

@app.command()
def saudi_arabia_geometric(
    strategy: str = typer.Option("optimal", "--strategy", "-s", help="Discovery strategy: optimal, efficient, comprehensive"),
    recreate_db: bool = typer.Option(False, "--recreate-db", help="Drop and recreate the database schema"),
    save_as_temp: Optional[str] = typer.Option(None, "--save-as-temp", help="Save parcels to a temporary table"),
):
    """🇸🇦 Run geometric pipeline for ALL Saudi provinces (comprehensive coverage)."""
    script = SCRIPT_DIR / "run_geometric_pipeline.py"
    cmd = [sys.executable, str(script), "--saudi-arabia", "--strategy", strategy]
    if recreate_db:
        cmd.append("--recreate-db")
    if save_as_temp:
        cmd += ["--save-as-temp", save_as_temp]
    subprocess.run(cmd, check=True)

@app.command()
def seed_tiles(
    province: Optional[str] = typer.Option(None, "--province", "-p", help="Province key as returned by settings.list_provinces(); if omitted, seeds all provinces unless --region-slugs set"),
    provinces: Optional[List[str]] = typer.Option(None, "--provinces", help="Multiple province keys"),
    region_slugs: Optional[List[str]] = typer.Option(None, "--region-slugs", help="Filter provinces by tile_url_template slug(s), e.g., riyadh, eastern_region"),
    status: str = typer.Option("pending", "--status", help="Initial status for seeded tiles"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of tiles per province (after stride)"),
    stride: int = typer.Option(1, "--stride", help="Take every Nth tile from bbox coverage"),
):
    """Seed the tile_urls table from province bbox metadata (z15) for one or all provinces.

    Use --limit and/or --stride to seed a small pilot sample.
    """
    from meshic_pipeline.config import settings
    from meshic_pipeline.utils.tile_list_generator import tiles_from_bbox_z
    from meshic_pipeline.persistence.db import get_db_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from meshic_pipeline.persistence.models import TileURL

    engine = get_db_engine(str(settings.database_url))
    session = Session(engine)
    # Determine province keys to seed
    provs = provinces or ([province] if province else None)
    if provs is None:
        if region_slugs:
            slugs = {s.lower() for s in region_slugs}
            provs = []
            for key in settings.list_provinces():
                meta = settings.get_province_meta(key)
                tpl = (meta.get("tile_url_template") or "").lower()
                for s in slugs:
                    if f"/{s}/" in tpl:
                        provs.append(key)
                        break
        else:
            provs = settings.list_provinces()
    if not provs:
        typer.echo("No provinces matched selection criteria.")
        raise typer.Exit(code=1)
    total = 0
    from urllib.parse import urlparse

    def normalize_base(tile_url_template: str) -> str:
        """Return base like https://host/maps/<region> regardless of template variations."""
        tpl = tile_url_template.strip()
        parts = urlparse(tpl)
        # last non-empty path segment as slug
        segs = [s for s in parts.path.split('/') if s]
        slug = segs[-1] if segs else ''
        base = f"{parts.scheme}://{parts.netloc}/maps/{slug}"
        return base

    for prov in provs:
        meta = settings.get_province_meta(prov)
        bbox = meta["bbox_z15"]
        tile_tuples = tiles_from_bbox_z(bbox, zoom=15)
        if stride and stride > 1:
            tile_tuples = tile_tuples[::stride]
        if limit is not None and limit >= 0:
            tile_tuples = tile_tuples[:limit]
        rows = []
        base = normalize_base(meta.get("tile_url_template", ""))
        for z, x, y in tile_tuples:
            url = f"{base}/{z}/{x}/{y}.vector.pbf"
            rows.append({
                "url": url,
                "zoom_level": z,
                "x": x,
                "y": y,
                "status": status,
            })
        if rows:
            stmt = pg_insert(TileURL).values(rows).on_conflict_do_nothing(index_elements=[TileURL.url])
            session.execute(stmt)
            session.commit()
            total += len(rows)
            typer.echo(f"Seeded {len(rows)} tiles for {prov}")
    typer.echo(f"Done. Seeded {total} tiles (before dedup).")

@app.command()
def db_geometric(
    batch_size: int = typer.Option(1000, "--batch-size", help="Tiles to claim per batch"),
    concurrency: int = typer.Option(5, "--concurrency", help="Initial concurrent HTTP requests (adaptive)"),
    request_delay: float = typer.Option(0.05, "--request-delay", help="Delay between requests (s)"),
    recreate_db: bool = typer.Option(False, "--recreate-db", help="Drop and recreate database schema"),
    save_as_temp: Optional[str] = typer.Option(None, "--save-as-temp", help="Save parcels to a temp table"),
    max_retries: int = typer.Option(5, "--max-retries", help="Max retries before permanent failure"),
    adaptive: bool = typer.Option(True, "--adaptive/--no-adaptive", help="Enable adaptive concurrency"),
):
    """Run geometric pipeline in DB-driven mode using the tile_urls queue."""
    script = SCRIPT_DIR / "run_db_geometric.py"
    cmd = [sys.executable, str(script),
           "--batch-size", str(batch_size),
           "--concurrency", str(concurrency),
           "--request-delay", str(request_delay),
           "--max-retries", str(max_retries)]
    if recreate_db:
        cmd.append("--recreate-db")
    if save_as_temp:
        cmd += ["--save-as-temp", save_as_temp]
    if adaptive:
        cmd.append("--adaptive")
    else:
        cmd.append("--no-adaptive")
    subprocess.run(cmd, check=True)

@app.command()
def discovery_summary():
    """📊 Show enhanced province discovery capabilities and statistics."""
    script = SCRIPT_DIR / "show_discovery_summary.py"
    cmd = [sys.executable, str(script)]
    subprocess.run(cmd, check=True)

@app.command()
def province_pipeline(
    province: str = typer.Argument(..., help="Province name: al_qassim, riyadh, madinah, asir, eastern, makkah"),
    strategy: str = typer.Option("optimal", "--strategy", "-s", help="Discovery strategy"),
    batch_size: int = typer.Option(300, "--batch-size", help="Enrichment batch size"),
    geometric_first: bool = typer.Option(True, "--geometric-first", help="Run geometric pipeline first"),
):
    """🚀 Complete province pipeline: geometric + enrichment for specific province."""
    script = SCRIPT_DIR / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "province-pipeline", 
           "--province", province, "--strategy", strategy, "--batch-size", str(batch_size)]
    if not geometric_first:
        cmd += ["--no-geometric-first"]
    subprocess.run(cmd, check=True)

@app.command()
def saudi_pipeline(
    strategy: str = typer.Option("efficient", "--strategy", "-s", help="Discovery strategy (efficient recommended for full country)"),
    batch_size: int = typer.Option(500, "--batch-size", help="Enrichment batch size"),
    geometric_first: bool = typer.Option(True, "--geometric-first", help="Run geometric pipeline first"),
):
    """🇸🇦 Complete Saudi Arabia pipeline: ALL provinces geometric + enrichment."""
    script = SCRIPT_DIR / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "saudi-pipeline", 
           "--strategy", strategy, "--batch-size", str(batch_size)]
    if not geometric_first:
        cmd += ["--no-geometric-first"]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    app()
