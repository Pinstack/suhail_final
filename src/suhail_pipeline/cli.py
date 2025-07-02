import typer
import subprocess
import sys
from typing import List, Optional
from pathlib import Path

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
    script = Path(__file__).parent.parent / "scripts" / "run_geometric_pipeline.py"
    cmd = [sys.executable, str(script)]
    if bbox:
        cmd += ["--bbox"] + [str(x) for x in bbox]
    if recreate_db:
        cmd.append("--recreate-db")
    if save_as_temp:
        cmd += ["--save-as-temp", save_as_temp]
    subprocess.run(cmd, check=True)

@app.command()
def enrich(
    mode: str = typer.Argument(
        "fast-enrich",
        help="Enrichment mode: fast-enrich, incremental-enrich, full-refresh, delta-enrich, smart-pipeline-enrich"
    ),
    batch_size: Optional[int] = typer.Option(
        None, "--batch-size", help="Number of parcels per batch"
    ),
    limit: Optional[int] = typer.Option(
        None, "--limit", help="Limit parcels for testing"
    ),
    *extra: str,
):
    """Run the enrichment pipeline (Stage 2)."""
    # Invoke the enrichment pipeline script directly
    script = Path(__file__).parent.parent / "scripts" / "run_enrichment_pipeline.py"
    cmd = [sys.executable, str(script), mode]
    if batch_size is not None:
        cmd += ["--batch-size", str(batch_size)]
    if limit is not None:
        cmd += ["--limit", str(limit)]
    if extra:
        cmd += list(extra)
    subprocess.run(cmd, check=True)

@app.command()
def monitor(
    action: str = typer.Argument(
        ..., help="Monitoring action: status, recommend, schedule-info"
    ),
):
    """Run enrichment monitoring commands."""
    # Invoke the monitoring script directly
    script = Path(__file__).parent.parent / "scripts" / "run_monitoring.py"
    cmd = [sys.executable, str(script), action]
    subprocess.run(cmd, check=True)

if __name__ == "__main__":
    app()
