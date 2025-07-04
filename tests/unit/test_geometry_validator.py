import geopandas as gpd
from shapely.geometry import Polygon

from src.meshic_pipeline.geometry.validator import validate_geometries


def test_validate_geometries_fixes_invalid_polygon():
    poly = Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])
    gdf = gpd.GeoDataFrame({"geometry": [poly]}, geometry="geometry", crs="EPSG:4326")

    validated = validate_geometries(gdf)

    assert not validated.empty
    assert validated.geometry.iloc[0].is_valid


def test_validate_geometries_empty():
    gdf = gpd.GeoDataFrame({"geometry": []}, geometry="geometry", crs="EPSG:4326")
    validated = validate_geometries(gdf)
    assert validated.empty
