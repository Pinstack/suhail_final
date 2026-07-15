"""Unit tests for the dimensions / building_detection write-mode plumbing:
- decode stamps `source_tile` and the synthetic `bd_id`, and they survive the
  SCHEMA_MAP column filter;
- `compute_synthetic_pk` is deterministic, geometry-sensitive, and keeps distinct
  rows distinct.
"""
import gzip
from pathlib import Path

import pytest
from shapely.geometry import Point

from suhail_pipeline.pipeline_orchestrator import decode_and_validate_tile
from suhail_pipeline.decoder.mvt_decoder import MVTDecoder
from suhail_pipeline.persistence.postgis_persister import (
    SCHEMA_MAP,
    TILE_SCOPED_LAYERS,
    SYNTHETIC_PK_CONFIG,
    compute_synthetic_pk,
)
from suhail_pipeline.config import settings

import geopandas as gpd

TILES = Path(__file__).resolve().parents[1] / "fixtures" / "suhail_live_2026_07" / "tiles"
DOWNTOWN = TILES / "riyadh_15_20636_14069.vector.pbf.gz"


def _decoded(layer):
    raw = DOWNTOWN.read_bytes()
    data = gzip.decompress(raw)
    out = decode_and_validate_tile((15, 20636, 14069), data, [layer], settings.default_crs)
    for name, gdf in out:
        if name == layer:
            return gdf
    return None


def _schema_filter(gdf, layer):
    gdf = MVTDecoder.apply_arabic_column_mapping(gdf)
    allowed = set(SCHEMA_MAP.get(layer, {}).keys()) | {"geometry"}
    return gdf[[c for c in gdf.columns if c in allowed]]


def test_config_wiring():
    assert "dimensions" in settings.layers_to_process
    assert "building_detection" in settings.layers_to_process
    # dimensions must NOT be keyed (would collapse edges); building_detection is synthetic-keyed
    assert settings.id_column_per_layer.get("dimensions") is None
    assert settings.id_column_per_layer.get("building_detection") == "bd_id"
    assert "dimensions" in TILE_SCOPED_LAYERS
    assert "building_detection" in SYNTHETIC_PK_CONFIG


def test_dimensions_source_tile_stamped_and_survives_filter():
    gdf = _decoded("dimensions")
    assert gdf is not None and len(gdf) > 100
    assert (gdf["source_tile"] == "15/20636/14069").all()
    filtered = _schema_filter(gdf, "dimensions")
    assert "source_tile" in filtered.columns
    assert {"parcel_objectid", "length_m", "azimuth"} <= set(filtered.columns)
    # many rows per parcel (edges) — confirms why it can't be keyed on parcel_objectid
    assert gdf["parcel_objectid"].nunique() < len(gdf)


def test_building_detection_synthetic_key_stamped_and_unique_enough():
    gdf = _decoded("building_detection")
    assert gdf is not None and len(gdf) > 100
    assert "bd_id" in gdf.columns
    assert (gdf["source_tile"] == "15/20636/14069").all()
    # every row got an id, and ids are (near-)unique for distinct geometries
    assert gdf["bd_id"].notna().all()
    assert gdf["bd_id"].nunique() >= len(gdf) * 0.99


def test_compute_synthetic_pk_is_deterministic_and_geometry_sensitive():
    g = gpd.GeoDataFrame(
        {"region_id": [10, 10], "class_pred": ["1", "1"], "prediction_year": [2025, 2025]},
        geometry=[Point(46.7, 24.6), Point(46.8, 24.7)],
        crs="EPSG:4326",
    )
    out1 = compute_synthetic_pk(g, "building_detection")
    out2 = compute_synthetic_pk(g, "building_detection")
    # deterministic
    assert list(out1["bd_id"]) == list(out2["bd_id"])
    # geometry-sensitive: same attrs, different geometry -> different id
    assert out1["bd_id"].iloc[0] != out1["bd_id"].iloc[1]
    # fits in a signed BIGINT
    assert all(0 <= v < 2**63 for v in out1["bd_id"])


def test_compute_synthetic_pk_noop_for_unconfigured_layer():
    g = gpd.GeoDataFrame({"a": [1]}, geometry=[Point(0, 0)], crs="EPSG:4326")
    out = compute_synthetic_pk(g, "parcels")
    assert "bd_id" not in out.columns
