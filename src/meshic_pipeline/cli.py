import typer
import subprocess
import sys
from typing import List, Optional
from pathlib import Path

# Determine project root (two levels up from this file)
SCRIPT_ROOT = Path(__file__).resolve().parents[2]

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
    # Invoke the geometric pipeline script directly
    script = SCRIPT_ROOT / "scripts" / "run_geometric_pipeline.py"
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
    script = SCRIPT_ROOT / "scripts" / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "fast-enrich", "--batch-size", str(batch_size)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    subprocess.run(cmd, check=True)

@app.command()
def incremental_enrich(
    batch_size: int = typer.Option(100, "--batch-size", help="Number of parcels per batch"),
    days_old: int = typer.Option(30, "--days-old", help="Days old threshold for stale data"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich parcels that haven't been updated in the specified number of days."""
    script = SCRIPT_ROOT / "scripts" / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "incremental-enrich", 
           "--batch-size", str(batch_size), "--days-old", str(days_old)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    subprocess.run(cmd, check=True)

@app.command()
def full_refresh(
    batch_size: int = typer.Option(50, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enrich ALL parcels with transaction prices (complete refresh)."""
    script = SCRIPT_ROOT / "scripts" / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "full-refresh", "--batch-size", str(batch_size)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    subprocess.run(cmd, check=True)

@app.command()
def delta_enrich(
    batch_size: int = typer.Option(200, "--batch-size", help="Number of parcels per batch"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit parcels for testing"),
    fresh_table: str = typer.Option("parcels_fresh_mvt", "--fresh-table", help="Fresh MVT table name"),
    auto_geometric: bool = typer.Option(False, "--auto-geometric", help="Auto-run geometric pipeline first"),
    show_details: bool = typer.Option(True, "--show-details/--no-details", help="Show change analysis"),
):
    """🎯 Delta enrichment: Only process parcels with actual transaction price changes (most efficient)."""
    script = SCRIPT_ROOT / "scripts" / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), "delta-enrich", 
           "--batch-size", str(batch_size), "--fresh-table", fresh_table]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    if auto_geometric:
        cmd += ["--auto-geometric"]
    if not show_details:
        cmd += ["--no-details"]
    subprocess.run(cmd, check=True)

@app.command()
def smart_pipeline(
    geometric_first: bool = typer.Option(True, "--geometric-first", help="Run geometric pipeline first"),
    batch_size: int = typer.Option(300, "--batch-size", help="Enrichment batch size"),
    bbox: Optional[List[float]] = typer.Option(None, "--bbox", help="Bounding box: W S E N"),
):
    """🧠 Smart pipeline: Complete geometric + enrichment workflow (recommended for full runs)."""
    script = SCRIPT_ROOT / "scripts" / "run_enrichment_pipeline.py"
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
    # Invoke the monitoring script directly
    script = SCRIPT_ROOT / "scripts" / "run_monitoring.py"
    cmd = [sys.executable, str(script), action]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    app()
