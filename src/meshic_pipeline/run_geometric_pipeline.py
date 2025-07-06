import asyncio
import logging
import subprocess
import sys
from typing import List, Tuple, Optional

import typer

from meshic_pipeline.pipeline_orchestrator import run_pipeline
from meshic_pipeline.config import settings

# Setup logging
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def main(
    bbox: List[float] = typer.Option(
        None,
        "--bbox",
        "-b",
        help="Bounding box in 'min_lon min_lat max_lon max_lat' format. Overrides the config grid.",
    ),
    province: Optional[str] = typer.Option(
        None,
        "--province",
        "-p",
        help="Saudi province name: al_qassim, riyadh, madinah, asir, eastern, makkah",
    ),
    strategy: str = typer.Option(
        "optimal",
        "--strategy",
        "-s",
        help="Discovery strategy: optimal, efficient, comprehensive",
    ),
    saudi_arabia: bool = typer.Option(
        False,
        "--saudi-arabia",
        help="Process ALL Saudi provinces (comprehensive coverage)",
    ),
    recreate_db: bool = typer.Option(
        False, "--recreate-db", help="Drop and recreate the database schema."
    ),
    save_as_temp: str = typer.Option(
        None,
        "--save-as-temp",
        help="Save the downloaded parcels to a temporary table with this name.",
    ),
    max_memory: Optional[int] = typer.Option(
        None,
        "--max-memory",
        help="Override memory limit in MB (default from config)",
    ),
    enable_monitoring: bool = typer.Option(
        True,
        "--enable-monitoring/--disable-monitoring",
        help="Enable memory monitoring and automatic GC",
    ),
):
    """
    🚀 Enhanced geometric processing pipeline with province discovery.
    
    Modes:
    - Default: Uses grid from pipeline_config.yaml  
    - Bbox: Traditional bounding box discovery
    - Province: Enhanced province discovery (--province al_qassim)
    - Saudi Arabia: All provinces (--saudi-arabia)
    """
    # Apply memory configuration overrides
    if max_memory is not None:
        settings.memory_config.max_memory_usage_mb = max_memory
    settings.memory_config.enable_memory_monitoring = enable_monitoring

    # Validation
    if bbox and len(bbox) != 4:
        logger.error("Bounding box must be 4 floats: min_lon min_lat max_lon max_lat")
        raise typer.Exit(code=1)
    
    if province and saudi_arabia:
        logger.error("Cannot specify both --province and --saudi-arabia")
        raise typer.Exit(code=1)
    
    if province:
        logger.info(f"🏛️ Processing province: {province}")
    if saudi_arabia:
        logger.info("🇸🇦 Processing ALL Saudi provinces")

    aoi_bbox = tuple(bbox) if bbox else None

    # Enhanced pipeline with province support
    asyncio.run(
        run_pipeline(
            aoi_bbox=aoi_bbox,
            zoom=settings.zoom,
            layers_override=settings.layers_to_process,
            recreate_db=recreate_db,
            save_as_temp=save_as_temp,
            province=province,
            strategy=strategy,
            saudi_arabia_mode=saudi_arabia,
        )
    )

if __name__ == "__main__":
    app() 
