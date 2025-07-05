import asyncio
import aiohttp
import json
import os
from pathlib import Path
import sys
import yaml

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from meshic_pipeline.config import settings
from meshic_pipeline.downloader.async_tile_downloader import AsyncTileDownloader
from meshic_pipeline.enrichment.api_client import SuhailAPIClient
from meshic_pipeline.logging_utils import get_logger

logger = get_logger(__name__)

def load_pipeline_config():
    """Load pipeline configuration from pipeline_config.yaml"""
    try:
        with open('pipeline_config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.error("pipeline_config.yaml not found. Ensure it's in the project root.")
        return {}

async def capture_real_fixtures():
    """Script to capture real MVT tiles and mock API responses as test fixtures."""
    logger.info("Starting fixture capture...")

    # Define fixture paths
    mvt_fixtures_dir = Path("tests/fixtures/mvt_tiles")
    api_fixtures_dir = Path("tests/fixtures/api_responses")
    
    mvt_fixtures_dir.mkdir(parents=True, exist_ok=True)
    api_fixtures_dir.mkdir(parents=True, exist_ok=True)

    # Load tile configuration from pipeline_config.yaml
    pipeline_config = load_pipeline_config()
    sample_z = pipeline_config.get('zoom', 15)
    sample_x = pipeline_config.get('center_x', 20636)
    sample_y = pipeline_config.get('center_y', 14069)

    # --- 1. Capture MVT Tile --- #
    tiles_to_capture = [
        (sample_z, sample_x, sample_y),
        (sample_z, sample_x + 1, sample_y), # Adjacent tile
        (sample_z + 1, (sample_x * 2) + 1, (sample_y * 2) + 1) # Tile at next zoom level
    ]
    
    logger.info(f"Capturing {len(tiles_to_capture)} sample MVT tiles...")
    async with AsyncTileDownloader() as downloader:
        downloaded_tiles = await downloader.download_many(tiles_to_capture)

    for tile_coords, tile_data in downloaded_tiles.items():
        z, x, y = tile_coords
        mvt_tile_path = mvt_fixtures_dir / f"sample_{z}_{x}_{y}.pbf"
        if tile_data:
            with open(mvt_tile_path, "wb") as f:
                f.write(tile_data)
            logger.info(f"✅ Captured MVT tile to {mvt_tile_path}")
        else:
            logger.warning(f"❌ Failed to capture MVT tile {z}/{x}/{y}.vector.pbf")
    
    # Create an empty tile fixture for edge case testing
    empty_tile_path = mvt_fixtures_dir / "empty_tile.pbf"
    with open(empty_tile_path, "wb") as f:
        # Creating an empty file
        pass
    logger.info(f"✅ Created empty tile fixture at {empty_tile_path}")

    # --- 2. Capture API Responses --- #
    # NOTE: You might need to replace 'YOUR_SAMPLE_PARCEL_OBJECT_ID' with an actual, stable parcel ID
    # from your database that has transactions, building rules, and price metrics.
    # For now, this will attempt to fetch with a dummy ID, which likely will return empty lists.
    sample_parcel_object_id = "1010002437301" # Replace with a real ID for actual data
    logger.info(f"Attempting to capture API responses for parcel_object_id: {sample_parcel_object_id}")

    connector = aiohttp.TCPConnector(limit_per_host=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        api_client = SuhailAPIClient(session)

        # Capture Transactions
        transactions = await api_client.fetch_transactions(sample_parcel_object_id)
        with open(api_fixtures_dir / "transactions_sample.json", "w") as f:
            json.dump([tx.raw_data for tx in transactions], f, indent=2)
        logger.info(f"✅ Captured {len(transactions)} sample transactions to {api_fixtures_dir / 'transactions_sample.json'}")

        # Capture Building Rules
        building_rules = await api_client.fetch_building_rules(sample_parcel_object_id)
        with open(api_fixtures_dir / "building_rules_sample.json", "w") as f:
            json.dump([rule.raw_data for rule in building_rules], f, indent=2)
        logger.info(f"✅ Captured {len(building_rules)} sample building rules to {api_fixtures_dir / 'building_rules_sample.json'}")

        # Capture Price Metrics (expects a list of parcel_object_ids)
        price_metrics = await api_client.fetch_price_metrics([sample_parcel_object_id])
        with open(api_fixtures_dir / "price_metrics_sample.json", "w") as f:
            json.dump([pm.dict(exclude_unset=True) for pm in price_metrics], f, indent=2)
        logger.info(f"✅ Captured {len(price_metrics)} sample price metrics to {api_fixtures_dir / 'price_metrics_sample.json'}")
    
    # Create empty/error response fixtures
    with open(api_fixtures_dir / "empty_response.json", "w") as f:
        json.dump({"status": True, "data": {}}, f, indent=2)
    logger.info("✅ Created empty_response.json fixture")

    with open(api_fixtures_dir / "error_response_500.json", "w") as f:
        json.dump({"status": False, "error": "Internal Server Error"}, f, indent=2)
    logger.info("✅ Created error_response_500.json fixture")

    logger.info("Fixture capture completed.")

if __name__ == "__main__":
    asyncio.run(capture_real_fixtures()) 
