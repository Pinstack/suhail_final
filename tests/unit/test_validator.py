import geopandas as gpd
from shapely.geometry import Polygon

from meshic_pipeline.geometry.validator import validate_geometries


def test_validate_geometries_empty():
    gdf = gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    result = validate_geometries(gdf)
    assert result.empty


def test_validate_geometries_fixes_invalid():
    poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    gdf = gpd.GeoDataFrame(geometry=[poly], crs="EPSG:4326")
    result = validate_geometries(gdf)
    assert result.geometry.iloc[0].is_valid
