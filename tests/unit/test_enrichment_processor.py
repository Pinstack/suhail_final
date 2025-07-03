import pytest
import asyncio
from unittest.mock import AsyncMock, patch
import aiohttp
from src.meshic_pipeline.enrichment.processor import fast_worker
from src.meshic_pipeline.persistence.models import Transaction, BuildingRule, ParcelPriceMetric
from src.meshic_pipeline.enrichment.api_client import SuhailAPIClient

@pytest.fixture
def mock_api_client():
    client = AsyncMock(spec=SuhailAPIClient)
    # Configure mock responses for fetch_transactions, fetch_building_rules, fetch_price_metrics
    client.fetch_transactions.return_value = [Transaction(transaction_id=1, parcel_objectid=1)]
    client.fetch_building_rules.return_value = [BuildingRule(building_rule_id="rule1", parcel_objectid=1)]
    client.fetch_price_metrics.return_value = [ParcelPriceMetric(parcel_objectid=1, average_price_of_meter=100.0)]
    return client

@pytest.mark.asyncio
async def test_fast_worker_success(mock_api_client):
    parcel_ids = ["parcel1", "parcel2", "parcel3"]
    batch_size = 2

    # Configure mock_api_client for multiple calls
    mock_api_client.fetch_transactions.side_effect = [
        [Transaction(transaction_id=1, parcel_objectid=1)],
        [Transaction(transaction_id=2, parcel_objectid=2)],
        [Transaction(transaction_id=3, parcel_objectid=3)],
    ]
    mock_api_client.fetch_building_rules.side_effect = [
        [BuildingRule(building_rule_id="rule1", parcel_objectid=1)],
        [BuildingRule(building_rule_id="rule2", parcel_objectid=2)],
        [BuildingRule(building_rule_id="rule3", parcel_objectid=3)],
    ]
    mock_api_client.fetch_price_metrics.side_effect = [
        [ParcelPriceMetric(parcel_objectid=1, average_price_of_meter=100.0), ParcelPriceMetric(parcel_objectid=2, average_price_of_meter=200.0)],
        [ParcelPriceMetric(parcel_objectid=3, average_price_of_meter=300.0)],
    ]

    all_transactions = []
    all_rules = []
    all_metrics = []

    async for transactions, rules, metrics in fast_worker(parcel_ids, batch_size, mock_api_client):
        all_transactions.extend(transactions)
        all_rules.extend(rules)
        all_metrics.extend(metrics)

    assert len(all_transactions) == 3
    assert len(all_rules) == 3
    assert len(all_metrics) == 3

    # Verify mock calls
    assert mock_api_client.fetch_transactions.call_count == 3
    assert mock_api_client.fetch_building_rules.call_count == 3
    assert mock_api_client.fetch_price_metrics.call_count == 2

@pytest.mark.asyncio
async def test_fast_worker_api_error(mock_api_client):
    parcel_ids = ["parcel1"]
    batch_size = 1

    mock_api_client.fetch_transactions.side_effect = aiohttp.ClientError("Connection error")
    mock_api_client.fetch_building_rules.return_value = []
    mock_api_client.fetch_price_metrics.return_value = []

    all_transactions = []
    all_rules = []
    all_metrics = []

    async for transactions, rules, metrics in fast_worker(parcel_ids, batch_size, mock_api_client):
        all_transactions.extend(transactions)
        all_rules.extend(rules)
        all_metrics.extend(metrics)

    assert len(all_transactions) == 0
    assert len(all_rules) == 0
    assert len(all_metrics) == 0

    assert mock_api_client.fetch_transactions.call_count == 1
    assert mock_api_client.fetch_building_rules.call_count == 1
    assert mock_api_client.fetch_price_metrics.call_count == 1
