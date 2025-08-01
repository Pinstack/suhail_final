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
