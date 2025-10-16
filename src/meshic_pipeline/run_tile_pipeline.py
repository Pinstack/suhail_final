import logging
import asyncio
import aiohttp
from sqlalchemy.orm import Session
from meshic_pipeline.persistence.db import get_db_engine
from meshic_pipeline.persistence.models import TileURL

BATCH_SIZE = 1000
MAX_RETRIES = 5

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("tile_pipeline")

async def process_tile(tile, session):
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(tile.url, timeout=30) as resp:
                if resp.status == 200:
                    logger.info(f"Processed tile: {tile.url}")
                    TileURL.update_status(session, tile.url, "processed")
                    return True
                else:
                    error = f"HTTP {resp.status}"
                    logger.error(f"Failed tile: {tile.url} ({error})")
                    # Check retry count for permanent failure
                    session.refresh(tile)
                    if tile.retry_count >= MAX_RETRIES:
                        TileURL.update_status(session, tile.url, "permanent_failed", error_message=error)
                    else:
                        TileURL.update_status(session, tile.url, "failed", error_message=error)
                    return False
    except Exception as e:
        error = str(e)
        logger.error(f"Exception for tile {tile.url}: {error}")
        session.refresh(tile)
        if tile.retry_count >= MAX_RETRIES:
            TileURL.update_status(session, tile.url, "permanent_failed", error_message=error)
        else:
            TileURL.update_status(session, tile.url, "failed", error_message=error)
        return False

def main():
    engine = get_db_engine()
    session = Session(engine)
    # Reset stale in_progress tiles
    reset_count = TileURL.reset_stale_in_progress(session, stale_minutes=60)
    if reset_count:
        logger.info(f"Reset {reset_count} stale in_progress tiles to failed.")
    loop = asyncio.get_event_loop()
    while True:
        tiles = TileURL.claim_tiles_for_processing(session, batch_size=BATCH_SIZE, max_retries=MAX_RETRIES)
        if not tiles:
            logger.info("No more pending or failed tiles to process. Exiting.")
            break
        tasks = [process_tile(tile, session) for tile in tiles]
        loop.run_until_complete(asyncio.gather(*tasks))
    session.close()

if __name__ == "__main__":
    main() 