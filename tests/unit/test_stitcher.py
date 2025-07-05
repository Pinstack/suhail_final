import geopandas as gpd
from meshic_pipeline.geometry.stitcher import GeometryStitcher

class DummyPersister:
    def __init__(self):
        self.sql = None
    def read_sql(self, sql, geom_col="geometry"):
        self.sql = sql
        return gpd.GeoDataFrame({"geometry": []})
    def drop_table(self, *args, **kwargs):
        pass
    def create_table_from_gdf(self, *args, **kwargs):
        pass
    def write(self, *args, **kwargs):
        pass


def test_dissolve_in_postgis_uses_point_extraction():
    p = DummyPersister()
    stitcher = GeometryStitcher("EPSG:4326", p)
    stitcher._dissolve_in_postgis("temp", "station_code", {}, "metro_stations")
    assert "CollectionExtract" in p.sql
    assert ", 1)" in p.sql


def test_dissolve_in_postgis_uses_polygon_extraction():
    p = DummyPersister()
    stitcher = GeometryStitcher("EPSG:4326", p)
    stitcher._dissolve_in_postgis("temp", "parcel_id", {}, "parcels")
    assert ", 3)" in p.sql
