import geopandas as gpd
from shapely.geometry import Point
from meshic_pipeline.geometry.stitcher import GeometryStitcher

class DummyPersister:
    def create_table_from_gdf(self, gdf, table_name, known_columns=None):
        pass
    def write(self, gdf, layer_name, table, if_exists="append"):
        pass
    def read_sql(self, sql):
        return gpd.GeoDataFrame({
            "parcel_id": [1],
            "geometry": [Point(0, 0)]
        }, geometry="geometry", crs="EPSG:4326")
    def drop_table(self, table):
        pass

def test_stitch_geometries_preserves_columns():
    gdf = gpd.GeoDataFrame({
        "parcel_id": [1],
        "geometry": [Point(0, 0)]
    }, geometry="geometry", crs="EPSG:4326")

    known_columns = ["parcel_id", "missing_col", "geometry"]
    stitcher = GeometryStitcher(target_crs="EPSG:4326", persister=DummyPersister())

    result = stitcher.stitch_geometries(
        [gdf],
        layer_name="parcels",
        id_column="parcel_id",
        agg_rules={},
        tiles=[],
        known_columns=known_columns,
    )

    assert "missing_col" in result.columns
    assert result["missing_col"].isna().all()
