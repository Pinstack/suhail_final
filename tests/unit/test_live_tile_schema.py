"""Contract tests: decode a real (gzipped) live Suhail MVT tile and assert the
decoder + canonical SCHEMA_MAP now capture the fields the 2026 tile schema exposes.

Fixture tiles captured 2026-07-15 (see docs/SUHAIL_SOURCE_AUDIT_2026-07.md).
The residential tile 20640/14060 contains parcels with recent transactions.
"""
import gzip
from pathlib import Path

import pytest

from suhail_pipeline.decoder.mvt_decoder import MVTDecoder
from suhail_pipeline.persistence.postgis_persister import SCHEMA_MAP

TILES = Path(__file__).resolve().parents[1] / "fixtures" / "suhail_live_2026_07" / "tiles"
RESIDENTIAL = TILES / "riyadh_15_20640_14060.vector.pbf.gz"  # z/x/y = 15/20640/14060
DOWNTOWN = TILES / "riyadh_15_20636_14069.vector.pbf.gz"     # has all 17 layers


def _decode(path, z, x, y):
    raw = path.read_bytes()
    data = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
    return MVTDecoder().decode_to_gdf(data, z, x, y)


def _schema_filter(gdf, layer):
    """Mimic the orchestrator: arabic-map then filter to SCHEMA_MAP columns."""
    gdf = MVTDecoder.apply_arabic_column_mapping(gdf)
    allowed = set(SCHEMA_MAP.get(layer, {}).keys()) | {"geometry"}
    return gdf[[c for c in gdf.columns if c in allowed]]


@pytest.fixture(scope="module")
def residential_layers():
    assert RESIDENTIAL.exists(), f"missing fixture tile {RESIDENTIAL}"
    return _decode(RESIDENTIAL, 15, 20640, 14060)


@pytest.fixture(scope="module")
def downtown_layers():
    assert DOWNTOWN.exists(), f"missing fixture tile {DOWNTOWN}"
    return _decode(DOWNTOWN, 15, 20636, 14069)


def test_expected_layers_present(downtown_layers):
    # The downtown tile carries the full transit + metrics layer set.
    for layer in ("parcels", "neighborhoods", "subdivisions", "bus_lines",
                  "metro_stations", "riyadh_bus_stations", "qi_population_metrics"):
        assert layer in downtown_layers, f"layer {layer} missing from live tile"


def test_parcels_market_timeseries_survive_schema_filter(residential_layers):
    gdf = _schema_filter(residential_layers["parcels"], "parcels")
    cols = set(gdf.columns)
    for f in (
        "transaction_price_1w", "transaction_price_12m",
        "price_of_meter_1m", "price_of_meter_6m",
        "transactions_count_12m", "transaction_date_12m",
        "zoning_group",
    ):
        assert f in cols, f"parcels field {f} dropped by schema filter"
    # Arabic neighbourhood name now retained on parcels.
    assert "neighborhood_ar" in cols


def test_parcels_have_nonzero_market_data(residential_layers):
    """At least some residential parcels carry real 12-month transaction data."""
    gdf = residential_layers["parcels"]
    assert "transactions_count_12m" in gdf.columns
    hits = (gdf["transactions_count_12m"].fillna(0).astype(float) > 0).sum()
    assert hits > 0, "expected some parcels with 12m transactions in this tile"


def test_bus_lines_fields_now_captured(downtown_layers):
    """Regression: bus_lines previously captured zero attributes (name mismatch)."""
    gdf = _schema_filter(downtown_layers["bus_lines"], "bus_lines")
    cols = set(gdf.columns)
    assert {"busroute", "color", "type"} <= cols
    assert len(gdf) > 0


def test_metro_stations_coordinates_captured(downtown_layers):
    gdf = _schema_filter(downtown_layers["metro_stations"], "metro_stations")
    assert {"station_long", "station_lat", "station_code"} <= set(gdf.columns)


def test_qi_population_metrics_reshaped_fields_captured(downtown_layers):
    gdf = _schema_filter(downtown_layers["qi_population_metrics"], "qi_population_metrics")
    cols = set(gdf.columns)
    for f in ("population_density", "rent_apartment", "purchasing_power", "poi_count"):
        assert f in cols, f"qi_population_metrics field {f} not captured"
