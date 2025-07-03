import pytest
import os
import gzip
from src.meshic_pipeline.decoder.mvt_decoder import MVTDecoder

@pytest.fixture
def mvt_decoder():
    return MVTDecoder()

@pytest.fixture
def tile_data():
    with gzip.open("test_tile.pbf", "rb") as f:
        return f.read()

def test_decode_mvt_to_gdf(mvt_decoder, tile_data):
    z, x, y = 15, 17208, 11069  # Example tile coordinates
    gdfs = mvt_decoder.decode_to_gdf(tile_data, z, x, y)

    assert isinstance(gdfs, dict)
    assert "parcels" in gdfs
    assert "dimensions" in gdfs

    parcels_gdf = gdfs["parcels"]
    assert not parcels_gdf.empty
    assert "geometry" in parcels_gdf.columns
    assert "parcel_objectid" in parcels_gdf.columns
    assert "subdivision_id" in parcels_gdf.columns

    
