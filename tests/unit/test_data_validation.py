import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from meshic_pipeline.persistence.postgis_persister import PostGISPersister

class MockPersister(PostGISPersister):
    def __init__(self):
        # Skip real database connection
        pass

def test_validate_and_cast_types_parcels():
    data = {
        "parcel_id": ["10", 20.0, None],
        "zoning_id": [1.0, 2.5, "3"],
        "transaction_price": ["100.5", 200, None],
        "purchase_date": ["2021-01-01", "not-a-date", None],
        "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
    }
    gdf = gpd.GeoDataFrame(data, geometry="geometry")

    persister = MockPersister()
    result = persister._validate_and_cast_types(gdf, layer_name="parcels")

    # parcel_id column should convert numeric strings and floats to integers
    assert result.loc[0, "parcel_id"] == 10
    assert result.loc[1, "parcel_id"] == 20
    assert pd.isna(result.loc[2, "parcel_id"])

    # zoning_id should cast fractional value to None
    assert result.loc[0, "zoning_id"] == 1
    assert pd.isna(result.loc[1, "zoning_id"])
    assert result.loc[2, "zoning_id"] == 3

    # transaction_price should be floats
    assert result.loc[0, "transaction_price"] == 100.5
    assert result.loc[1, "transaction_price"] == 200.0
    assert pd.isna(result.loc[2, "transaction_price"])

    # purchase_date should be converted to datetime64
    assert pd.api.types.is_datetime64_any_dtype(result["purchase_date"])
    assert pd.isna(result.loc[1, "purchase_date"])  # invalid date becomes NaT


def test_validate_and_cast_types_handles_bigint_strings():
    data = {
        "subdivision_id": ["101000319.0", 101000320.0, "not-an-int"],
        "geometry": [Point(0, 0), Point(1, 1), Point(2, 2)],
    }
    gdf = gpd.GeoDataFrame(data, geometry="geometry")

    persister = MockPersister()
    result = persister._validate_and_cast_types(gdf, layer_name="parcels")

    assert result.loc[0, "subdivision_id"] == 101000319
    assert result.loc[1, "subdivision_id"] == 101000320
    assert pd.isna(result.loc[2, "subdivision_id"])
    assert str(result["subdivision_id"].dtype) == "Int64"
