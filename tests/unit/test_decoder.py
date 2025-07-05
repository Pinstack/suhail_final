from meshic_pipeline.decoder.mvt_decoder import MVTDecoder
import geopandas as gpd
import shapely.geometry


def test_decode_empty_bytes():
    decoder = MVTDecoder()
    assert decoder.decode_bytes(b"", 15, 0, 0) == {}


def test_cast_property_types_basic():
    decoder = MVTDecoder()
    result = decoder._cast_property_types({"parcel_id": "1", "other": "abc"})
    assert result["parcel_id"] == 1
    assert result["other"] == "abc"


def test_apply_arabic_column_mapping():
    gdf = gpd.GeoDataFrame(
        {
            "neighborhaname": ["حي"],
            "geometry": [shapely.geometry.Point(0, 0)],
        },
        geometry="geometry",
        crs="EPSG:4326",
    )
    mapped = MVTDecoder.apply_arabic_column_mapping(gdf)
    assert "neighborhood_ar" in mapped.columns
    assert "neighborhaname" not in mapped.columns
