import argparse
import asyncio
from src.suhail_pipeline.pipeline_orchestrator import run_pipeline

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