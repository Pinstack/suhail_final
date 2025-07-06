#!/usr/bin/env python3
"""
Fast Enrichment Pipeline - Optimized for Speed
Processes only unprocessed parcels with aggressive performance tuning.
"""

import asyncio
import aiohttp
import typer
from typing import List, Optional
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.dialects.postgresql import insert as pg_insert
from datetime import datetime, timedelta

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from meshic_pipeline.persistence.models import (
    Base,
    Transaction,
    ParcelPriceMetric,
    BuildingRule,
)
from meshic_pipeline.config import settings
import logging
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import ForeignKey
from meshic_pipeline.exceptions import ValidationException
from meshic_pipeline.logging_utils import get_logger
from meshic_pipeline.enrichment.strategies import (
    get_unprocessed_parcel_ids,
    get_stale_parcel_ids,
    get_delta_parcel_ids,
    get_all_enrichable_parcel_ids,
    get_delta_parcel_ids_with_details,
)
from meshic_pipeline.enrichment.processor import fast_worker
from meshic_pipeline.persistence.db import (
    get_async_db_engine,
    setup_database_async,
)
from meshic_pipeline.persistence.enrichment_persister import (
    fast_store_batch_data,
)
from meshic_pipeline.enrichment.api_client import SuhailAPIClient
from rich import print as rprint

logger = get_logger(__name__)
app = typer.Typer()
Base = declarative_base()


def exit_with_error(summary: str, hint: str) -> None:
    """Print a formatted error message and exit."""
    rprint(f"[bold red]❌ ERROR: {summary}[/bold red]")
    rprint(f"[bold yellow]   💡 HINT: {hint}[/bold yellow]")
    raise typer.Exit(code=1)


async def _table_exists(engine: AsyncEngine, table: str) -> bool:
    """Check if the given table exists in the public schema."""
    query = text("SELECT to_regclass(:tbl)")
    async with engine.begin() as conn:
        result = await conn.scalar(query, {"tbl": f"public.{table}"})
        return result is not None

async def run_enrichment_for_ids(
    parcel_ids: List[str], batch_size: int, process_name: str
):
    """Generic function to run the enrichment process for a list of parcel IDs."""
    if not parcel_ids:
        logger.info(f"No parcels to process for {process_name}.")
        return

    logger.info(
        f"Starting {process_name} for {len(parcel_ids)} parcels with batch size {batch_size}"
    )

    async_engine = get_async_db_engine()
    async_session_factory = async_sessionmaker(async_engine, expire_on_commit=False)
    total_tx = total_rules = total_metrics = 0

    connector = aiohttp.TCPConnector(limit_per_host=50)
    async with aiohttp.ClientSession(connector=connector) as session:
        api_client = SuhailAPIClient(session)
        
        async for transactions, rules, metrics in fast_worker(
            parcel_ids, batch_size, api_client
        ):
            if not transactions and not rules and not metrics:
                continue

            async with async_session_factory() as db_session:
                tx_count, rules_count, metrics_count = await fast_store_batch_data(
                    db_session, transactions, rules, metrics
                )
                total_tx += tx_count
                total_rules += rules_count
                total_metrics += metrics_count

    logger.info(
        f"Finished {process_name}. Added {total_tx} transactions, {total_rules} building rules, {total_metrics} price metrics."
    )
    return total_tx, total_rules, total_metrics

async def _run_enrichment(strategy_func, engine, batch_size, limit, **kwargs):
    """A single async function to orchestrate the entire enrichment process."""
    await setup_database_async(engine)
    parcel_ids = await strategy_func(engine, limit=limit, **kwargs)
    await run_enrichment_for_ids(parcel_ids, batch_size, strategy_func.__name__)

@app.command()
def fast_enrich(
    batch_size: int = typer.Option(
        200, "--batch-size", help="Number of parcels per batch"
    ),
    limit: int = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enriches new parcels."""
    engine = get_async_db_engine()
    asyncio.run(_run_enrichment(get_unprocessed_parcel_ids, engine, batch_size, limit))

@app.command()
def incremental_enrich(
    batch_size: int = typer.Option(
        100, "--batch-size", help="Number of parcels per batch"
    ),
    days_old: int = typer.Option(30, "--days-old", help="Days old threshold"),
    limit: int = typer.Option(None, "--limit", help="Limit parcels for testing"),
):
    """Enriches stale parcels."""
    engine = get_async_db_engine()
    asyncio.run(
        _run_enrichment(
            get_stale_parcel_ids, engine, batch_size, limit, days_old=days_old
        )
    )

@app.command()
def full_refresh(
    batch_size: int = typer.Option(50, "--batch-size", help="Batch size"),
    limit: int = typer.Option(None, "--limit", help="Limit parcels"),
):
    """Enriches all enrichable parcels."""
    engine = get_async_db_engine()
    asyncio.run(
        _run_enrichment(get_all_enrichable_parcel_ids, engine, batch_size, limit)
    )

@app.command()
def delta_enrich(
    batch_size: int = typer.Option(
        200, "--batch-size", help="Number of parcels per batch"
    ),
    limit: int = typer.Option(None, "--limit", help="Limit parcels for testing"),
    fresh_mvt_table: str = typer.Option(
        "parcels_fresh_mvt", "--fresh-table", help="Name of fresh MVT data table"
    ),
    show_details: bool = typer.Option(
        True, "--show-details/--no-details", help="Show detailed change analysis"
    ),
    auto_run_geometric: bool = typer.Option(
        False, "--auto-geometric", help="Automatically run geometric pipeline first"
    ),
):
    """🎯 DELTA ENRICHMENT: MVT-based change detection - only enrich parcels with actual transaction price changes."""
    typer.echo("\n🎯 DELTA ENRICHMENT - MVT Change Detection")
    typer.echo("Only processes parcels where transaction_price changed in MVT tiles")
    typer.echo("Maximum efficiency: Real market signal detection")
    typer.echo("=" * 70)
    
    async def run_delta_enrichment():
        engine = get_async_db_engine()

        start_time = datetime.utcnow()
        auto_created_table = False
        metrics = {}
        enrichment_status = "failed"

        try:
            if auto_run_geometric:
                typer.echo("🏗️ Auto-running geometric pipeline to get fresh MVT data...")
                try:
                    import subprocess
                    import sys
                    from pathlib import Path

                    script_path = Path(__file__).parent / "run_geometric_pipeline.py"
                    result = subprocess.run(
                        [
                            sys.executable,
                            str(script_path),
                            "--layers",
                            "parcels",
                            "--save-temp-table",
                            fresh_mvt_table,
                        ],
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode == 0:
                        typer.echo("✅ Geometric pipeline completed successfully")
                        typer.echo(f"📊 Fresh MVT data saved to table: {fresh_mvt_table}")
                        auto_created_table = True
                    else:
                        exit_with_error(
                            "Geometric pipeline failed to create fresh data table.",
                            "Check the pipeline logs and retry."
                        )
                except Exception as e:
                    exit_with_error(
                        f"Error running geometric pipeline: {e}",
                        "Ensure the geometric pipeline is functional."
                    )

            if not await _table_exists(engine, fresh_mvt_table):
                exit_with_error(
                    f'The specified fresh data table "{fresh_mvt_table}" does not exist.',
                    "Verify the table name or use the '--auto-geometric' flag to create it automatically."
                )

            async with engine.begin() as conn:
                db_count = await conn.scalar(text("SELECT COUNT(*) FROM public.parcels"))
                mvt_count = await conn.scalar(text(f"SELECT COUNT(*) FROM public.{fresh_mvt_table}"))

            if show_details:
                parcel_ids, change_stats = await get_delta_parcel_ids_with_details(
                    engine, fresh_mvt_table, limit
                )

                if change_stats:
                    typer.echo(f"\n📊 CHANGE DETECTION ANALYSIS:")
                    typer.echo(f"  Total changes detected: {len(parcel_ids):,}")
                    for change_type, count in change_stats.items():
                        type_desc = {
                            'new_parcel_with_transaction': 'New parcels with transactions',
                            'null_to_positive': 'Previously null → positive price',
                            'zero_to_positive': 'Previously zero → positive price',
                            'price_changed': 'Transaction price changed',
                            'price_disappeared': 'Price disappeared',
                        }.get(change_type, change_type)
                        typer.echo(f"  • {type_desc}: {count:,}")
            else:
                parcel_ids = await get_delta_parcel_ids(engine, fresh_mvt_table, limit)
                change_stats = {}

            metrics["parcels_scanned_in_db"] = db_count
            metrics["parcels_scanned_from_mvt"] = mvt_count

            if not parcel_ids:
                typer.echo("\n✅ No transaction price changes detected!")
                typer.echo("All parcels are up-to-date. No enrichment needed.")
                enrichment_status = "success"
                return

            typer.echo(f"\n🎯 Processing {len(parcel_ids):,} parcels with detected changes...")
            tx_count, rules_count, metrics_count = await run_enrichment_for_ids(parcel_ids, batch_size, "DELTA")

            metrics.update({
                "enriched_transactions_count": tx_count,
                "enriched_rules_count": rules_count,
                "enriched_metrics_count": metrics_count,
            })
            enrichment_status = "success"

            duration = datetime.utcnow() - start_time
            typer.echo("\n✅ Delta Enrichment Complete!\n")
            typer.echo("--- Run Summary ---")
            typer.echo(f"Duration:          {int(duration.total_seconds())}s")
            typer.echo(f"Changes Detected:  {len(parcel_ids)} parcels")
            for ctype, count in change_stats.items():
                typer.echo(f"  - {ctype}: {count}")
            typer.echo("Records Created:")
            typer.echo(f"  - Transactions:  {tx_count}")
            typer.echo(f"  - Building Rules: {rules_count}")
            typer.echo(f"  - Price Metrics:  {metrics_count}")

            metrics.update({
                "run_timestamp_utc": start_time.isoformat() + "Z",
                "run_duration_seconds": duration.total_seconds(),
                "strategy": "delta_enrichment",
                "parcels_identified_for_enrichment": len(parcel_ids),
                "change_statistics": change_stats,
                "enrichment_status": enrichment_status,
            })

            logger.info("Delta enrichment run completed successfully.", extra={"metrics": metrics})

        finally:
            if auto_created_table:
                typer.echo("🧹 Cleaning up auto-generated temporary table...")
                try:
                    from src.meshic_pipeline.persistence.postgis_persister import PostGISPersister
                    persister = PostGISPersister(str(settings.database_url))
                    persister.drop_table(fresh_mvt_table)
                    typer.echo(f"🧹 Cleaned up temporary table: {fresh_mvt_table}")
                except Exception as e:
                    typer.echo(f"⚠️ Warning: Could not clean up temp table: {e}")
    
    asyncio.run(run_delta_enrichment())

@app.command()
def smart_pipeline_enrich(
    geometric_first: bool = typer.Option(True, "--geometric-first", help="Run geometric pipeline first"),
    trigger_after: bool = typer.Option(True, "--trigger-after", help="Run fast enrichment after geometric"),
    batch_size: int = typer.Option(300, "--batch-size", help="Enrichment batch size"),
    bbox: List[float] = typer.Option(None, "--bbox", help="Bounding box: W S E N")
):
    """
    🧠 SMART PIPELINE: Combines geometric processing with intelligent enrichment.
    
    This is the OPTIMAL strategy that:
    1. Runs Stage 1 (geometric) to reveal parcels with transaction_price > 0
    2. Immediately enriches those parcels with detailed transaction data
    3. Guarantees capture of all new transaction data
    
    Perfect for: Complete pipeline runs, maximum efficiency and coverage
    """
    print("🧠 Starting SMART PIPELINE with geometric + fast enrichment...")
    
    if geometric_first:
        print("\n🗺️  STAGE 1: Running geometric pipeline...")
        from run_pipeline import main as run_geometric_pipeline
        import sys
        
        # Prepare args for geometric pipeline
        geo_args = ["run_pipeline.py"]
        if bbox and len(bbox) == 4:
            geo_args.extend(["--bbox"] + [str(x) for x in bbox])
        
        # Save original sys.argv and replace it
        original_argv = sys.argv
        sys.argv = geo_args
        
        try:
            run_geometric_pipeline()
            print("✅ Geometric pipeline completed!")
        finally:
            sys.argv = original_argv
    
    if trigger_after:
        print("\n🎯 STAGE 2: Running fast enrichment...")
        fast_enrich.callback(
            batch_size=batch_size,
            limit=None,
        )

if __name__ == "__main__":
    app() 
