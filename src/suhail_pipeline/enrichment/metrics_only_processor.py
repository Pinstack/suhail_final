"""
Specialized processor for price metrics only enrichment.
"""

from typing import AsyncGenerator, List, Tuple
from suhail_pipeline.enrichment.api_client import SuhailAPIClient
from suhail_pipeline.persistence.models import Transaction, BuildingRule, ParcelPriceMetric
from suhail_pipeline.logging_utils import get_logger
import asyncio

logger = get_logger(__name__)

async def metrics_only_worker(
    parcel_ids: List[str], batch_size: int, api_client: SuhailAPIClient
) -> AsyncGenerator[Tuple[List[Transaction], List[BuildingRule], List[ParcelPriceMetric]], None]:
    """
    Process parcels in batches to get only price metrics.
    Skips transactions and building rules APIs which fail for most parcels.
    
    Args:
        parcel_ids: List of parcel object IDs to process
        batch_size: Number of parcels to process per batch
        api_client: Configured API client
        
    Yields:
        Tuples of ([], [], price_metrics) - empty lists for transactions and rules
    """
    
    for i in range(0, len(parcel_ids), batch_size):
        batch = parcel_ids[i : i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(parcel_ids) + batch_size - 1) // batch_size
        
        logger.info(
            f"🎯 Processing metrics-only batch {batch_num}/{total_batches} ({len(batch)} parcels)"
        )
        
        try:
            # Only fetch price metrics - skip failing APIs
            price_metrics = await api_client.fetch_price_metrics(batch)
            
            # Log results
            metrics_count = len(price_metrics) if price_metrics else 0
            logger.info(f"📊 Batch {batch_num}: {metrics_count} price metrics retrieved")
            
            # Return empty lists for transactions and building rules
            yield [], [], price_metrics or []
            
        except Exception as e:
            logger.error(f"❌ Error processing metrics batch {batch_num}: {e}")
            # Yield empty results to continue processing
            yield [], [], []
            
        # Small delay to be respectful to API
        await asyncio.sleep(0.1)
