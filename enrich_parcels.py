import asyncio
import aiohttp
import typer
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import List
import logging
from sqlalchemy import (
    Table, Column, Integer, String, Float, DateTime, BigInteger, JSON, ForeignKey,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy import tuple_
import uuid

from src.suhail_pipeline.config import settings

# --- Basic Setup ---
app = typer.Typer()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Database Setup ---
Base = declarative_base()

# Define the existing 'parcels' table structure for relationship purposes
parcels_table = Table('parcels', Base.metadata,
    Column('parcel_objectid', String, primary_key=True),
    schema='public',
    extend_existing=True
)

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(BigInteger, primary_key=True)
    parcel_objectid = Column(String, ForeignKey('public.parcels.parcel_objectid'))
    transaction_price = Column(Float)
    price_of_meter = Column(Float)
    transaction_date = Column(DateTime)
    area = Column(Float)
    # Storing the rest as JSON for simplicity
    raw_data = Column(JSON)

class ParcelPriceMetric(Base):
    __tablename__ = 'parcel_price_metrics'
    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    parcel_objectid = Column(String, ForeignKey('public.parcels.parcel_objectid'))
    month = Column(Integer)
    year = Column(Integer)
    metrics_type = Column(String)
    average_price_of_meter = Column(Float)
    __table_args__ = (UniqueConstraint('parcel_objectid', 'month', 'year', 'metrics_type', name='_parcel_metric_uc'),)

class BuildingRule(Base):
    __tablename__ = 'building_rules'
    parcel_objectid = Column(String, ForeignKey('public.parcels.parcel_objectid'), primary_key=True)
    rule_id = Column(String)
    zoning_id = Column(Integer)
    zoning_color = Column(String)
    zoning_group = Column(String)
    landuse = Column(String)
    description = Column(String)
    name = Column(String)
    coloring = Column(String)
    coloring_description = Column(String)
    max_building_coefficient = Column(String)
    max_building_height = Column(String)
    max_parcel_coverage = Column(String)
    max_rule_depth = Column(String)
    main_streets_setback = Column(String)
    secondary_streets_setback = Column(String)
    side_rear_setback = Column(String)
    raw_data = Column(JSON)

def get_db_engine():
    """Creates and returns a SQLAlchemy engine."""
    return create_engine(str(settings.database_url))

def setup_database(engine):
    """Creates the necessary tables if they don't exist."""
    logger.info("Setting up database tables...")
    Base.metadata.create_all(engine, checkfirst=True)
    logger.info("Tables checked/created successfully.")

def get_db_session(engine):
    """Provides a SQLAlchemy session."""
    Session = sessionmaker(bind=engine)
    return Session()

# --- API Interaction ---
async def fetch_transactions(session: aiohttp.ClientSession, parcel_objectid: str) -> List[Transaction]:
    """Fetches and parses transaction data for a single parcel with retries."""
    url = f"https://api2.suhail.ai/transactions?parcelObjectId={parcel_objectid}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with session.get(url) as response:
                if response.status >= 500:
                    response.raise_for_status() # Will be caught by ClientResponseError
                
                # For 4xx errors, we don't retry, just log and exit for this parcel
                if 400 <= response.status < 500:
                    logger.warning(f"Client error {response.status} for {url}. Not retrying.")
                    return []

                response.raise_for_status() # For other errors
                
                data = await response.json()
                if not data or not data.get("status") or "data" not in data or not data["data"].get("transactions"):
                    return []
                
                new_transactions = []
                for tx_data in data["data"]["transactions"]:
                    new_tx = Transaction(
                        transaction_id=tx_data.get("transactionNumber"),
                        parcel_objectid=parcel_objectid,
                        transaction_price=tx_data.get("transactionPrice"),
                        price_of_meter=tx_data.get("priceOfMeter"),
                        transaction_date=tx_data.get("transactionDate"),
                        area=tx_data.get("area"),
                        raw_data=tx_data
                    )
                    new_transactions.append(new_tx)
                return new_transactions # Success
        except aiohttp.ClientResponseError as e:
            if e.status >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Server error {e.status} for {url}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"HTTP Error fetching transactions for {parcel_objectid}: {e}")
                return [] # Failed after all retries
        except Exception as e:
            logger.error(f"Error processing transaction data for {parcel_objectid}: {e}")
            return []
    return []

async def fetch_building_rules(session: aiohttp.ClientSession, parcel_objectid: str) -> List[BuildingRule]:
    """Fetches and parses building rules for a single parcel with retries."""
    url = f"https://api2.suhail.ai/parcel/buildingRules?parcelObjectId={parcel_objectid}"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with session.get(url) as response:
                if response.status >= 500:
                    response.raise_for_status()

                if 400 <= response.status < 500:
                    logger.warning(f"Client error {response.status} for {url}. Not retrying.")
                    return []
                
                response.raise_for_status()

                data = await response.json()
                if not data or not data.get("status") or "data" not in data or not data["data"]:
                    return []

                new_rules = []
                for rule_data in data["data"]:
                    new_rule = BuildingRule(
                        parcel_objectid=parcel_objectid,
                        rule_id=rule_data.get("id"),
                        zoning_id=rule_data.get("zoningId"),
                        zoning_color=rule_data.get("zoningColor"),
                        zoning_group=rule_data.get("zoningGroup"),
                        landuse=rule_data.get("landuse"),
                        description=rule_data.get("description"),
                        name=rule_data.get("name"),
                        coloring=rule_data.get("coloring"),
                        coloring_description=rule_data.get("coloringDescription"),
                        max_building_coefficient=rule_data.get("maxBuildingCoefficient"),
                        max_building_height=rule_data.get("maxBuildingHeight"),
                        max_parcel_coverage=rule_data.get("maxParcelCoverage"),
                        max_rule_depth=rule_data.get("maxRuleDepth"),
                        main_streets_setback=rule_data.get("mainStreetsSetback"),
                        secondary_streets_setback=rule_data.get("secondaryStreetsSetback"),
                        side_rear_setback=rule_data.get("sideRearSetback"),
                        raw_data=rule_data
                    )
                    new_rules.append(new_rule)
                return new_rules
        except aiohttp.ClientResponseError as e:
            if e.status >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Server error {e.status} for {url}. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"HTTP Error fetching building rules for {parcel_objectid}: {e}")
                return []
        except Exception as e:
            logger.error(f"Error processing building rules data for {parcel_objectid}: {e}")
            return []
    return []

async def fetch_price_metrics(session: aiohttp.ClientSession, parcel_objectids: List[str]) -> List[ParcelPriceMetric]:
    """Fetches and parses price metrics for a batch of parcels with retries."""
    base_url = "https://api2.suhail.ai/api/parcel/metrics/priceOfMeter"
    params = [("parcelObjsIds", pid) for pid in parcel_objectids]
    params.append(("groupingType", "Monthly"))
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with session.get(base_url, params=params) as response:
                if response.status >= 500:
                    response.raise_for_status()
                
                if 400 <= response.status < 500:
                    logger.warning(f"Client error {response.status} for metrics batch. Not retrying.")
                    return []

                response.raise_for_status()
                
                data = await response.json()

                if not data or not data.get("status") or "data" not in data:
                    return []
                
                new_metrics = []
                for parcel_data in data["data"]:
                    pid = parcel_data.get("parcelObjId")
                    for metric_data in parcel_data.get("parcelMetrics", []):
                        new_metric = ParcelPriceMetric(
                            parcel_objectid=pid,
                            month=metric_data.get("month"),
                            year=metric_data.get("year"),
                            metrics_type=metric_data.get("metricsType"),
                            average_price_of_meter=metric_data.get("avaragePriceOfMeter")
                        )
                        new_metrics.append(new_metric)
                return new_metrics
        except aiohttp.ClientResponseError as e:
            if e.status >= 500 and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Server error {e.status} for metrics batch. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"HTTP Error fetching metrics for batch: {e}")
                return []
        except Exception as e:
            logger.error(f"Error processing metrics data: {e}")
            return []
    return []

async def main_worker(parcel_ids: List[str], batch_size: int):
    """Main async worker to coordinate fetching and storing."""
    engine = get_db_engine()
    
    async with aiohttp.ClientSession() as http_session:
        for i in range(0, len(parcel_ids), batch_size):
            batch_ids = parcel_ids[i:i+batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(parcel_ids) + batch_size - 1)//batch_size}...")

            # --- Create concurrent tasks ---
            transaction_tasks = [fetch_transactions(http_session, pid) for pid in batch_ids]
            rules_tasks = [fetch_building_rules(http_session, pid) for pid in batch_ids]
            metrics_task = fetch_price_metrics(http_session, batch_ids)

            # --- Gather results ---
            all_transaction_results = await asyncio.gather(*transaction_tasks)
            all_rules_results = await asyncio.gather(*rules_tasks)
            metrics_results = await metrics_task
            
            # Flatten the list of lists of transactions
            transactions_to_add = [tx for sublist in all_transaction_results for tx in sublist]
            rules_to_add = [rule for sublist in all_rules_results for rule in sublist]

            # --- Commit to DB ---
            db_session = get_db_session(engine)
            committed_tx_count = 0
            committed_metrics_count = 0
            committed_rules_count = 0
            try:
                # --- Process Transactions using ON CONFLICT ---
                if transactions_to_add:
                    insert_values = [
                        {
                            "transaction_id": tx.transaction_id,
                            "parcel_objectid": tx.parcel_objectid,
                            "transaction_price": tx.transaction_price,
                            "price_of_meter": tx.price_of_meter,
                            "transaction_date": tx.transaction_date,
                            "area": tx.area,
                            "raw_data": tx.raw_data,
                        }
                        for tx in transactions_to_add
                    ]
                    if insert_values:
                        stmt = pg_insert(Transaction).values(insert_values)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['transaction_id'])
                        result = db_session.execute(stmt)
                        committed_tx_count = result.rowcount

                # --- Process Metrics using ON CONFLICT ---
                if metrics_results:
                    insert_values = [
                        {
                            "parcel_objectid": m.parcel_objectid,
                            "month": m.month,
                            "year": m.year,
                            "metrics_type": m.metrics_type,
                            "average_price_of_meter": m.average_price_of_meter,
                        }
                        for m in metrics_results
                    ]
                    if insert_values:
                        stmt = pg_insert(ParcelPriceMetric).values(insert_values)
                        stmt = stmt.on_conflict_do_nothing(index_elements=['parcel_objectid', 'month', 'year', 'metrics_type'])
                        result = db_session.execute(stmt)
                        committed_metrics_count = result.rowcount

                # --- Process Building Rules using ON CONFLICT ---
                if rules_to_add:
                    # Deduplicate rules based on parcel_objectid, keeping the last one seen
                    unique_rules = {rule.parcel_objectid: rule for rule in rules_to_add}
                    rules_to_add = list(unique_rules.values())
                    
                    insert_values = [
                        {
                            "parcel_objectid": r.parcel_objectid,
                            "rule_id": r.rule_id,
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
                        for r in rules_to_add
                    ]
                    if insert_values:
                        stmt = pg_insert(BuildingRule).values(insert_values)
                        # Update existing rule with new data if it conflicts.
                        update_dict = {c.name: getattr(stmt.excluded, c.name) for c in BuildingRule.__table__.c if not c.primary_key}
                        stmt = stmt.on_conflict_do_update(
                            index_elements=['parcel_objectid'],
                            set_=update_dict
                        )
                        result = db_session.execute(stmt)
                        committed_rules_count = result.rowcount

                db_session.commit()
                logger.info(f"Committed {committed_tx_count} new transactions, {committed_metrics_count} new metrics, and {committed_rules_count} updated/new building rules for batch.")
            except Exception as e:
                logger.error(f"Database Error: {e}")
                db_session.rollback()
                raise
            finally:
                db_session.close()


# --- Main Application Logic ---
@app.command()
def enrich(
    batch_size: int = typer.Option(100, "--batch-size", help="Number of parcels to process in one API call for metrics."),
    limit: int = typer.Option(None, "--limit", help="Limit the number of parcels to process for testing."),
    full_scan: bool = typer.Option(False, "--full-scan", help="Run enrichment on all parcels, not just those with transaction prices > 0."),
):
    """
    Enriches the parcels data by fetching additional information from Suhail APIs.
    By default, it only processes parcels that have a transaction_price > 0.
    """
    logger.info("Starting enrichment process...")
    engine = get_db_engine()

    # 1. Get parcel IDs from DB
    db_session = get_db_session(engine)
    
    if full_scan:
        logger.info("Running in --full-scan mode. Querying all parcels.")
        query = "SELECT parcel_objectid FROM public.parcels WHERE parcel_objectid IS NOT NULL"
    else:
        logger.info("Running in efficient mode. Querying only parcels with transaction_price > 0.")
        query = "SELECT parcel_objectid FROM public.parcels WHERE transaction_price > 0"

    if limit:
        query += f" LIMIT {limit}"
    
    result = db_session.execute(text(query))
    parcel_ids = [row[0] for row in result]
    logger.info(f"Found {len(parcel_ids):,} parcel object IDs to enrich.")

    # 2. Setup database tables (idempotently)
    setup_database(engine)

    # 3. Fetch and store data in batches
    asyncio.run(main_worker(parcel_ids, batch_size))
    
    logger.info("Enrichment process finished.")


@app.command()
def test_fetch(
    parcel_objectid: str = typer.Option("101000620207", "--parcel-id", help="Specific Parcel Object ID to test fetching for."),
):
    """
    Fetches and prints all available data for a single parcel without saving to the DB.
    """
    logger.info(f"--- Testing data fetching for Parcel ID: {parcel_objectid} ---")

    async def _test_worker():
        async with aiohttp.ClientSession() as http_session:
            # --- Create concurrent tasks ---
            transaction_task = fetch_transactions(http_session, parcel_objectid)
            rules_task = fetch_building_rules(http_session, parcel_objectid)
            metrics_task = fetch_price_metrics(http_session, [parcel_objectid])

            # --- Gather results ---
            transactions = await transaction_task
            rules = await rules_task
            metrics = await metrics_task
            
            # --- Print results ---
            logger.info("--- Fetched Building Rules ---")
            if rules:
                import json
                for rule in rules:
                    print(json.dumps(rule.raw_data, indent=2, ensure_ascii=False))
            else:
                logger.info("No building rules found.")

            logger.info("\n--- Fetched Transactions ---")
            if transactions:
                import json
                for tx in transactions:
                    print(json.dumps(tx.raw_data, indent=2, ensure_ascii=False))
            else:
                logger.info("No transactions found.")

            logger.info("\n--- Fetched Price Metrics ---")
            if metrics:
                for metric in metrics:
                    # A bit cleaner than __dict__
                    print({c.name: getattr(metric, c.name) for c in metric.__table__.c})
            else:
                logger.info("No price metrics found.")

    asyncio.run(_test_worker())
    logger.info(f"--- Finished testing for Parcel ID: {parcel_objectid} ---")


if __name__ == "__main__":
    app() 