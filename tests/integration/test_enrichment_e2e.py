import os
import pytest
import asyncio
from sqlalchemy import text
from meshic_pipeline.cli import _run_enrichment_async
from meshic_pipeline.persistence.db import get_db_engine, setup_database
from meshic_pipeline.persistence.models import Transaction, BuildingRule, ParcelPriceMetric
from meshic_pipeline.enrichment.api_client import SuhailAPIClient
from meshic_pipeline.config import settings

@ pytest.fixture(scope="module")
def test_db_engine():
    # Use an isolated database for testing
    test_url = "postgresql://postgres:postgres@localhost:5432/meshic_integration_test"
    os.environ["DATABASE_URL"] = test_url
    settings.database_url = test_url
    engine = get_db_engine()
    # Create enrichment tables
    setup_database(engine)
    # Clear any existing enrichment or parcel rows, then insert a dummy parcel
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM public.transactions"))
        conn.execute(text("DELETE FROM public.building_rules"))
        conn.execute(text("DELETE FROM public.parcel_price_metrics"))
        conn.execute(text("DELETE FROM public.parcels"))
        conn.execute(text(
            "INSERT INTO public.parcels (parcel_objectid, transaction_price, geometry, is_active) "
            "VALUES (123456, 100.0, ST_GeomFromText('MULTIPOLYGON(((0 0,0 1,1 1,1 0,0 0)))',4326), TRUE)"
        ))
    return engine

# Mark test as asyncio
@pytest.mark.asyncio
async def test_enrichment_pipeline_persists_data(monkeypatch, test_db_engine):
    # Stub API client methods to return one record each
    async def stub_fetch_transactions(self, parcel_objectid):
        return [Transaction(
            transaction_id=1,
            parcel_objectid=parcel_objectid,
            transaction_price=50.0,
            price_of_meter=5.0,
            transaction_date=None,
            area=100.0,
            raw_data={}
        )]

    async def stub_fetch_building_rules(self, parcel_objectid):
        return [BuildingRule(
            parcel_objectid=parcel_objectid,
            building_rule_id="rule1",
            zoning_id=1,
            zoning_color="red",
            zoning_group="grp",
            landuse="lu",
            description="desc",
            name="rule-name",
            coloring="col",
            coloring_description="cd",
            max_building_coefficient="1.0",
            max_building_height="10",
            max_parcel_coverage="0.5",
            max_rule_depth="1",
            main_streets_setback="1",
            secondary_streets_setback="2",
            side_rear_setback="3",
            raw_data={}
        )]

    async def stub_fetch_price_metrics(self, parcel_objectids):
        pid = parcel_objectids[0]
        return [ParcelPriceMetric(
            parcel_objectid=pid,
            month=1,
            year=2025,
            metrics_type="type",
            average_price_of_meter=10.0
        )]

    monkeypatch.setattr(SuhailAPIClient, 'fetch_transactions', stub_fetch_transactions)
    monkeypatch.setattr(SuhailAPIClient, 'fetch_building_rules', stub_fetch_building_rules)
    monkeypatch.setattr(SuhailAPIClient, 'fetch_price_metrics', stub_fetch_price_metrics)

    # Run the enrichment pipeline against our test DB
    await _run_enrichment_async(mode="fast-enrich", batch_size=None, limit=None)

    # Verify at least one record was persisted in each table
    with test_db_engine.connect() as conn:
        tx_count = conn.execute(text("SELECT COUNT(*) FROM public.transactions")).scalar_one()
        rules_count = conn.execute(text("SELECT COUNT(*) FROM public.building_rules")).scalar_one()
        metrics_count = conn.execute(text("SELECT COUNT(*) FROM public.parcel_price_metrics")).scalar_one()

    assert tx_count == 1
    assert rules_count == 1
    assert metrics_count == 1 