from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from datetime import datetime, timedelta

from meshic_pipeline.logging_utils import get_logger

logger = get_logger(__name__)


async def get_unprocessed_parcel_ids(
    engine: AsyncEngine, limit: Optional[int] = None
) -> List[str]:
    """
    Get parcel IDs that have a transaction price but have not yet been enriched.
    This is the primary strategy for new data.

    Query is optimized to use `NOT EXISTS` which is generally faster for large
    tables than a `LEFT JOIN / IS NULL` check.
    
    Recommended Index:
        CREATE INDEX IF NOT EXISTS idx_parcels_parcel_objectid ON public.parcels (parcel_objectid);
        CREATE INDEX IF NOT EXISTS idx_transactions_parcel_objectid ON public.transactions (parcel_objectid);
    """
    query = """
        SELECT p.parcel_objectid
        FROM public.parcels p
        WHERE p.transaction_price > 0
          AND NOT EXISTS (
            SELECT 1
            FROM public.transactions t
            WHERE t.parcel_objectid = p.parcel_objectid
          )
        ORDER BY p.parcel_objectid
    """

    if limit:
        query += f" LIMIT {limit}"

    async with engine.begin() as conn:
        result = await conn.execute(text(query))
        parcel_ids = [row[0] for row in result]

    logger.info(f"Found {len(parcel_ids):,} unprocessed parcels to enrich.")
    return parcel_ids


async def get_all_enrichable_parcel_ids(
    engine: AsyncEngine, limit: Optional[int] = None
) -> List[str]:
    """
    Get ALL parcels that have transaction_price > 0.
    Used for full data refreshes.
    """
    query = """
        SELECT parcel_objectid FROM public.parcels
        WHERE transaction_price > 0
        ORDER BY parcel_objectid
    """

    if limit:
        query += f" LIMIT {limit}"

    async with engine.begin() as conn:
        result = await conn.execute(text(query))
        parcel_ids = [row[0] for row in result]

    logger.info(
        f"Found {len(parcel_ids):,} enrichable parcels (including previously processed)."
    )
    return parcel_ids


async def get_stale_parcel_ids(
    engine: AsyncEngine, days_old: int = 30, limit: Optional[int] = None
) -> List[str]:
    """
    Get parcels that haven't been enriched recently.
    This query is optimized to only check the `parcels` table, assuming
    `enriched_at` is reliably updated.
    
    Recommended Index:
        CREATE INDEX IF NOT EXISTS idx_parcels_enriched_at ON public.parcels (enriched_at);
    """
    query = """
        SELECT parcel_objectid
        FROM public.parcels
        WHERE transaction_price > 0
          AND (enriched_at IS NULL OR enriched_at < :cutoff_date)
        ORDER BY parcel_objectid
    """

    cutoff_date = datetime.now() - timedelta(days=days_old)

    if limit:
        query += f" LIMIT {limit}"

    async with engine.begin() as conn:
        result = await conn.execute(text(query), {"cutoff_date": cutoff_date})
        parcel_ids = [row[0] for row in result]

    logger.info(f"Found {len(parcel_ids):,} parcels not enriched in last {days_old} days.")
    return parcel_ids


async def get_delta_parcel_ids(
    engine: AsyncEngine, 
    fresh_mvt_table: str = "parcels_fresh_mvt",
    limit: Optional[int] = None
) -> List[str]:
    """
    Get parcel IDs where the MVT transaction_price differs from stored values.
    This implements the MVT-based change detection strategy.
    
    Args:
        engine: Database engine
        fresh_mvt_table: Temporary table name containing fresh MVT data
        limit: Optional limit on results
        
    Returns:
        List of parcel_objectid strings that need enrichment due to price changes
    """
    query = """
        WITH price_changes AS (
            SELECT 
                COALESCE(p.parcel_objectid, f.parcel_objectid) as parcel_objectid,
                p.transaction_price as stored_price,
                f.transaction_price as mvt_price,
                CASE 
                    WHEN p.parcel_objectid IS NULL THEN 'new_parcel_with_transaction'
                    WHEN p.transaction_price IS NULL AND f.transaction_price > 0 THEN 'null_to_positive'
                    WHEN p.transaction_price = 0 AND f.transaction_price > 0 THEN 'zero_to_positive'
                    WHEN p.transaction_price != f.transaction_price THEN 'price_changed'
                    ELSE 'no_change'
                END as change_type
            FROM public.parcels p
            FULL OUTER JOIN public.{fresh_mvt_table} f 
                ON p.parcel_objectid = f.parcel_objectid
            WHERE f.transaction_price > 0  -- Only consider parcels with transactions in MVT
        )
        SELECT parcel_objectid 
        FROM price_changes 
        WHERE change_type != 'no_change'
        ORDER BY parcel_objectid
    """.format(fresh_mvt_table=fresh_mvt_table)

    if limit:
        query += f" LIMIT {limit}"

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(query))
            parcel_ids = [row[0] for row in result]

        logger.info(
            f"Found {len(parcel_ids):,} parcels with transaction price changes requiring enrichment."
        )
        return parcel_ids
        
    except Exception as e:
        logger.error(f"Error detecting price changes: {e}")
        logger.info("Fresh MVT table may not exist. Run geometric pipeline first.")
        return []


async def get_delta_parcel_ids_with_details(
    engine: AsyncEngine,
    fresh_mvt_table: str = "parcels_fresh_mvt",
    limit: Optional[int] = None
) -> tuple[List[str], dict]:
    """
    Get delta parcels with detailed change statistics for monitoring.
    
    Returns:
        Tuple of (parcel_ids, change_stats)
    """
    query = """
        WITH price_changes AS (
            SELECT 
                COALESCE(p.parcel_objectid, f.parcel_objectid) as parcel_objectid,
                p.transaction_price as stored_price,
                f.transaction_price as mvt_price,
                CASE 
                    WHEN p.parcel_objectid IS NULL THEN 'new_parcel_with_transaction'
                    WHEN p.transaction_price IS NULL AND f.transaction_price > 0 THEN 'null_to_positive'
                    WHEN p.transaction_price = 0 AND f.transaction_price > 0 THEN 'zero_to_positive'
                    WHEN p.transaction_price != f.transaction_price THEN 'price_changed'
                    ELSE 'no_change'
                END as change_type
            FROM public.parcels p
            FULL OUTER JOIN public.{fresh_mvt_table} f 
                ON p.parcel_objectid = f.parcel_objectid
            WHERE f.transaction_price > 0
        )
        SELECT 
            parcel_objectid,
            change_type,
            stored_price,
            mvt_price
        FROM price_changes 
        WHERE change_type != 'no_change'
        ORDER BY parcel_objectid
    """.format(fresh_mvt_table=fresh_mvt_table)

    if limit:
        query += f" LIMIT {limit}"

    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()

        parcel_ids = [row[0] for row in rows]
        
        # Generate change statistics
        change_stats = {}
        for row in rows:
            change_type = row[1]
            change_stats[change_type] = change_stats.get(change_type, 0) + 1

        logger.info(f"Delta enrichment analysis:")
        logger.info(f"  Total parcels requiring enrichment: {len(parcel_ids):,}")
        for change_type, count in change_stats.items():
            logger.info(f"  {change_type}: {count:,}")

        return parcel_ids, change_stats
        
    except Exception as e:
        logger.error(f"Error detecting price changes with details: {e}")
        return [], {} 