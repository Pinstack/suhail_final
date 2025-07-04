import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection
from sqlalchemy.engine import Result
from sqlalchemy import text

from src.meshic_pipeline.enrichment.strategies import (
    get_unprocessed_parcel_ids,
    get_all_enrichable_parcel_ids,
    get_stale_parcel_ids,
    get_delta_parcel_ids,
    get_delta_parcel_ids_with_details,
)

@pytest.fixture
def mock_async_engine():
    engine = AsyncMock(spec=AsyncEngine)
    conn = AsyncMock(spec=AsyncConnection)
    engine.begin.return_value.__aenter__.return_value = conn
    conn.execute.return_value = mock_result
    return engine

@pytest.fixture
def mock_result():
    result = AsyncMock(spec=Result)
    return result

def test_get_unprocessed_parcel_ids_success(mock_async_engine, mock_result):
    expected_ids = ["parcel1", "parcel2", "parcel3"]
    rows = [(pid,) for pid in expected_ids]
    mock_result.__iter__.return_value = iter(rows)
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_unprocessed_parcel_ids(mock_async_engine)

    parcel_ids = asyncio.run(run())

    assert parcel_ids == expected_ids
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()
    # You can add more specific assertions about the query if needed

def test_get_unprocessed_parcel_ids_empty(mock_async_engine, mock_result):
    mock_result.__iter__.return_value = iter([])
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_unprocessed_parcel_ids(mock_async_engine)

    parcel_ids = asyncio.run(run())

    assert parcel_ids == []
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()

def test_get_all_enrichable_parcel_ids_success(mock_async_engine, mock_result):
    expected_ids = ["parcelA", "parcelB"]
    rows = [(pid,) for pid in expected_ids]
    mock_result.__iter__.return_value = iter(rows)
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_all_enrichable_parcel_ids(mock_async_engine)

    parcel_ids = asyncio.run(run())

    assert parcel_ids == expected_ids
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()

def test_get_stale_parcel_ids_success(mock_async_engine, mock_result):
    expected_ids = ["stale1", "stale2"]
    rows = [(pid,) for pid in expected_ids]
    mock_result.__iter__.return_value = iter(rows)
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_stale_parcel_ids(mock_async_engine, days_old=7)

    parcel_ids = asyncio.run(run())

    assert parcel_ids == expected_ids
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()
    # You can add assertions to check the 'cutoff_date' parameter in the execute call

def test_get_delta_parcel_ids_success(mock_async_engine, mock_result):
    expected_ids = ["delta1", "delta2"]
    rows = [(pid,) for pid in expected_ids]
    mock_result.__iter__.return_value = iter(rows)
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_delta_parcel_ids(mock_async_engine, fresh_mvt_table="test_table")

    parcel_ids = asyncio.run(run())

    assert parcel_ids == expected_ids
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()

def test_get_delta_parcel_ids_with_details_success(mock_async_engine, mock_result):
    mock_rows = [
        ("delta_detail1", "new_parcel_with_transaction", 0.0, 100.0),
        ("delta_detail2", "price_changed", 50.0, 150.0),
    ]
    expected_ids = [row[0] for row in mock_rows]
    expected_stats = {"new_parcel_with_transaction": 1, "price_changed": 1}

    mock_result.fetchall.return_value = mock_rows
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.return_value = mock_result

    async def run():
        return await get_delta_parcel_ids_with_details(mock_async_engine, fresh_mvt_table="test_table")

    parcel_ids, change_stats = asyncio.run(run())

    assert parcel_ids == expected_ids
    assert change_stats == expected_stats
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()

def test_get_delta_parcel_ids_exception(mock_async_engine):
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.side_effect = Exception("DB Error")

    async def run():
        return await get_delta_parcel_ids(mock_async_engine)

    parcel_ids = asyncio.run(run())

    assert parcel_ids == []
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()

def test_get_delta_parcel_ids_with_details_exception(mock_async_engine):
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.side_effect = Exception("DB Error with details")

    async def run():
        return await get_delta_parcel_ids_with_details(mock_async_engine)

    parcel_ids, change_stats = asyncio.run(run())

    assert parcel_ids == []
    assert change_stats == {}
    mock_async_engine.begin.return_value.__aenter__.return_value.execute.assert_called_once()
