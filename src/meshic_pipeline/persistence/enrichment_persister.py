from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import text
from math import ceil

from .models import Transaction, BuildingRule, ParcelPriceMetric
from meshic_pipeline.logging_utils import get_logger

logger = get_logger(__name__)


async def fast_store_batch_data(
    async_session: AsyncSession,
    transactions: List[Transaction],
    rules: List[BuildingRule],
    metrics: List[ParcelPriceMetric],
) -> tuple[int, int, int]:
    """Optimized batch storage with minimal overhead. Now with safe batching to avoid SQL parameter overflow."""

    PARAMETER_LIMIT = 32000  # Safe upper bound for PostgreSQL

    def get_batch_size(num_columns: int) -> int:
        return max(1, PARAMETER_LIMIT // num_columns)

    # Bulk insert transactions
    tx_count = 0
    if transactions:
        tx_values = [
            {
                "transaction_id": tx.transaction_id,
                "parcel_objectid": int(tx.parcel_objectid),
                "transaction_price": tx.transaction_price,
                "price_of_meter": tx.price_of_meter,
                "transaction_date": tx.transaction_date,
                "area": tx.area,
                "raw_data": tx.raw_data,
            }
            for tx in transactions
        ]
        num_cols = len(tx_values[0]) if tx_values else 1
        batch_size = get_batch_size(num_cols)
        for i in range(0, len(tx_values), batch_size):
            batch = tx_values[i:i+batch_size]
            stmt = pg_insert(Transaction).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=["transaction_id"])
            result = await async_session.execute(stmt)
            tx_count += result.rowcount or 0

    # Bulk insert rules (deduplicated)
    rules_count = 0
    if rules:
        unique_rules = {rule.parcel_objectid: rule for rule in rules}
        rules_values = [
            {
                "parcel_objectid": int(r.parcel_objectid),
                "building_rule_id": r.building_rule_id,
                "zoning_id": r.zoning_id,
                "zoning_color": r.zoning_color,
                "zoning_group": r.zoning_group,
                "landuse": r.landuse,
                "description": r.description,
                "name": r.name,
                "coloring": r.coloring,
                "coloring_description": r.coloring_description,
                "max_building_coefficient": r.max_building_coefficient,
                "max_building_height": r.max_building_height,
                "max_parcel_coverage": r.max_parcel_coverage,
                "max_rule_depth": r.max_rule_depth,
                "main_streets_setback": r.main_streets_setback,
                "secondary_streets_setback": r.secondary_streets_setback,
                "side_rear_setback": r.side_rear_setback,
                "raw_data": r.raw_data,
            }
            for r in unique_rules.values()
        ]
        num_cols = len(rules_values[0]) if rules_values else 1
        batch_size = get_batch_size(num_cols)
        for i in range(0, len(rules_values), batch_size):
            batch = rules_values[i:i+batch_size]
            stmt = pg_insert(BuildingRule).values(batch)
            stmt = stmt.on_conflict_do_nothing(index_elements=["parcel_objectid", "building_rule_id"])
            result = await async_session.execute(stmt)
            rules_count += result.rowcount or 0

    # Bulk insert metrics
    metrics_count = 0
    if metrics:
        metrics_values = [
            {
                "parcel_objectid": int(m.parcel_objectid),
                "month": m.month,
                "year": m.year,
                "metrics_type": m.metrics_type,
                "average_price_of_meter": m.average_price_of_meter,
            }
            for m in metrics
        ]
        num_cols = len(metrics_values[0]) if metrics_values else 1
        batch_size = get_batch_size(num_cols)
        for i in range(0, len(metrics_values), batch_size):
            batch = metrics_values[i:i+batch_size]
            stmt = pg_insert(ParcelPriceMetric).values(batch)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["parcel_objectid", "month", "year", "metrics_type"]
            )
            result = await async_session.execute(stmt)
            metrics_count += result.rowcount or 0

    # Update enrichment timestamp for processed parcels
    if transactions or rules or metrics:
        processed_parcel_ids = set()
        if transactions:
            processed_parcel_ids.update(
                int(tx.parcel_objectid) for tx in transactions
            )
        if rules:
            processed_parcel_ids.update(int(r.parcel_objectid) for r in rules)
        if metrics:
            processed_parcel_ids.update(int(m.parcel_objectid) for m in metrics)

        if processed_parcel_ids:
            # Update enriched_at timestamp
            update_stmt = text(
                """
                UPDATE public.parcels
                SET enriched_at = NOW()
                WHERE parcel_objectid = ANY(:parcel_ids)
            """
            )
            await async_session.execute(
                update_stmt, {"parcel_ids": list(processed_parcel_ids)}
            )

    await async_session.commit()
    return tx_count, rules_count, metrics_count 
