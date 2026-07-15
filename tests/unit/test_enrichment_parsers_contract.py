"""Contract tests: parse real captured Suhail API payloads through the enrichment
parsers and assert the fields we now promise to capture actually survive.

Fixtures were captured live on 2026-07-15 (see docs/SUHAIL_SOURCE_AUDIT_2026-07.md)
and live under tests/fixtures/suhail_live_2026_07/api/.
"""
import json
from pathlib import Path

import pytest

from suhail_pipeline.enrichment.api_client import (
    parse_transactions_payload,
    parse_building_rules_payload,
    parse_price_metrics_payload,
)
from suhail_pipeline.persistence.enrichment_persister import fast_store_batch_data  # noqa: F401  (import guard)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "suhail_live_2026_07" / "api"


def _load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_transactions_payload_promotes_market_attributes():
    data = _load("transactions__9941681.json")
    txs = parse_transactions_payload(data, 9941681)
    assert txs, "fixture parcel 9941681 should have transactions"

    tx = txs[0]
    # Legacy fields still captured.
    assert tx.transaction_id is not None
    assert tx.transaction_price is not None
    assert tx.price_of_meter is not None
    assert tx.transaction_date is not None
    # Newly-promoted attributes (previously only in raw_data).
    assert tx.transaction_type is not None       # "type"
    assert tx.property_type is not None           # "propertyType"
    assert tx.metrics_type is not None            # "metricsType"
    assert tx.land_use_group is not None          # landUseGroup / landUsageGroup
    assert tx.transaction_source is not None      # "transactionSource"
    assert isinstance(tx.subdivision_id, int)     # string in source, coerced to int
    assert isinstance(tx.neighborhood_id, int)
    assert tx.is_low_value_transaction is not None
    # raw_data preserved in full.
    assert tx.raw_data.get("transactionNumber") == tx.transaction_id


def test_transactions_empty_payload_is_safe():
    empty = {"data": {"transactions": []}, "status": True}
    assert parse_transactions_payload(empty, 1) == []
    assert parse_transactions_payload({}, 1) == []


def test_building_rules_payload_captures_all_setback_fields():
    data = _load("buildingRules__9858274.json")
    rules = parse_building_rules_payload(data, 9858274)
    assert len(rules) >= 1
    r = rules[0]
    assert r.building_rule_id is not None
    assert r.max_building_coefficient is not None
    assert r.max_building_height is not None
    assert r.max_parcel_coverage is not None
    # setback fields must survive
    assert r.main_streets_setback is not None
    assert r.secondary_streets_setback is not None
    assert r.side_rear_setback is not None


def test_building_rules_multiple_rules_are_not_collapsed():
    """The persister must key on (parcel_objectid, building_rule_id), not parcel alone."""
    data = {
        "status": True,
        "data": [
            {"id": "RULE-A", "zoningId": 1},
            {"id": "RULE-B", "zoningId": 2},
        ],
    }
    rules = parse_building_rules_payload(data, 555)
    assert len(rules) == 2
    dedup = {(r.parcel_objectid, r.building_rule_id): r for r in rules}
    assert len(dedup) == 2, "two distinct rules for one parcel must both survive dedup"


def test_price_metrics_payload_sets_neighborhood_id():
    data = _load("priceOfMeter__9858274.json")
    metrics = parse_price_metrics_payload(data)
    assert metrics, "fixture should yield neighborhood metrics"
    # Every metric must now carry a neighborhood_id (previously always NULL).
    assert all(m.neighborhood_id is not None for m in metrics)
    m = metrics[0]
    assert m.month is not None and m.year is not None
    assert m.metrics_type is not None
    assert m.average_price_of_meter is not None
