import asyncio
import aiohttp
from typing import List, AsyncGenerator, Tuple

from meshic_pipeline.enrichment.api_client import SuhailAPIClient
from meshic_pipeline.persistence.models import (
    Transaction,
    BuildingRule,
    ParcelPriceMetric,
)
from meshic_pipeline.logging_utils import get_logger
from meshic_pipeline.persistence.db import get_async_db_engine
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = get_logger(__name__)


async def fast_worker(
    parcel_ids: List[str], batch_size: int, api_client: SuhailAPIClient
) -> AsyncGenerator[Tuple[List[Transaction], List[BuildingRule], List[ParcelPriceMetric]], None]:
    """
    Highly concurrent, memory-efficient worker that fetches enrichment data
    for a list of parcel IDs and yields results batch by batch.
    """
    total_batches = (len(parcel_ids) + batch_size - 1) // batch_size
    
    for i in range(0, len(parcel_ids), batch_size):
        batch_ids = parcel_ids[i : i + batch_size]
        batch_num = i // batch_size + 1
        logger.info(f"🚀 Processing batch {batch_num}/{total_batches} ({len(batch_ids)} parcels)")

        # Create all API call tasks for the current batch
        transaction_tasks = [api_client.fetch_transactions(pid) for pid in batch_ids]
        rules_tasks = [api_client.fetch_building_rules(pid) for pid in batch_ids]
        metrics_task = api_client.fetch_price_metrics(batch_ids)

        try:
            # Execute all tasks for the batch concurrently
            results = await asyncio.gather(
                asyncio.gather(*transaction_tasks, return_exceptions=True),
                asyncio.gather(*rules_tasks, return_exceptions=True),
                metrics_task,
                return_exceptions=True,
            )
            
            # Unpack results, handling potential top-level failures
            all_tx_results = results[0] if not isinstance(results[0], Exception) else []
            all_rules_results = results[1] if not isinstance(results[1], Exception) else []
            metrics_results = results[2] if not isinstance(results[2], Exception) else []

        except Exception as e:
            logger.error(f"Batch {batch_num} failed entirely: {e}")
            continue

        # Filter out any individual failed API calls within the batch
        transactions_to_add = [res for res in all_tx_results if not isinstance(res, Exception) for res in res]
        rules_to_add = [res for res in all_rules_results if not isinstance(res, Exception) for res in res]

        # Yield the successfully fetched data for this batch
        yield transactions_to_add, rules_to_add, metrics_results 
