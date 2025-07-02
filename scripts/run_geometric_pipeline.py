import asyncio
import logging
from typing import List, Tuple

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
    recreate_db: bool = typer.Option(
        False, "--recreate-db", help="Drop and recreate the database schema."
    ),
    save_as_temp: str = typer.Option(
        None,
        "--save-as-temp",
        help="Save the downloaded parcels to a temporary table with this name.",
    ),
):
    """
    Run the geometric processing pipeline to download and stitch MVT data.
    By default, it uses the grid defined in pipeline_config.yaml.
    """
    if bbox and len(bbox) != 4:
        logger.error("Bounding box must be 4 floats: min_lon min_lat max_lon max_lat")
        raise typer.Exit(code=1)

    aoi_bbox = tuple(bbox) if bbox else None

    # The orchestrator will handle discovery based on whether a bbox is provided
    asyncio.run(
        run_pipeline(
            aoi_bbox=aoi_bbox,
            zoom=settings.zoom,
            layers_override=settings.layers_to_process,
            recreate_db=recreate_db,
            save_as_temp=save_as_temp,
        )
    )

if __name__ == "__main__":
    app() 