import asyncio
import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon
import mapbox_vector_tile
import sqlalchemy

from meshic_pipeline.pipeline_orchestrator import run_pipeline
from meshic_pipeline.config import settings

# Integration test that exercises the pipeline orchestration with mocked
# downloader and database persistence.


def test_run_pipeline_with_mocks(monkeypatch):
    import sqlalchemy
    # Patch inspect in orchestrator to always return a mock with has_table True
    class DummyInspector:
        def has_table(self, table_name, schema=None):
            return True
    monkeypatch.setattr("meshic_pipeline.pipeline_orchestrator.inspect", lambda engine: DummyInspector())
    # Patch reset_temp_table to a no-op
    monkeypatch.setattr("meshic_pipeline.pipeline_orchestrator.reset_temp_table", lambda *a, **kw: None)

    # sample tile with a single parcel feature
    tile_bytes = mapbox_vector_tile.encode(
        {
            "name": "parcels",
            "features": [
                {
                    "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    "properties": {"parcel_id": 1},
                }
            ],
        },
        quantize_bounds=(0, 0, 1, 1),
        extents=4096,
    )

    # discovery returns exactly one tile coordinate
    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.get_tile_coordinates_for_bounds",
        lambda bbox, zoom: [(15, 0, 0)],
    )

    # dummy downloader yields the sample tile data
    class DummyDownloader:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def download_many(self, tiles):
            return {tiles[0]: tile_bytes}

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.AsyncTileDownloader",
        DummyDownloader,
    )

    # collect persisted GeoDataFrames for assertion
    persisted = {}
    temp_tables = {}

    class DummyPersister:
        def __init__(self, *args, **kwargs):
            self.engine = None

        def write(
            self,
            gdf,
            layer_name,
            table,
            if_exists="append",
            id_column=None,
            schema="public",
            chunksize=5000,
            geometry_type=None,
        ):
            if table.startswith("temp"):
                temp_tables.setdefault(table, []).append(gdf)
            else:
                persisted[layer_name] = gdf

        def recreate_database(self):
            pass

        def execute(self, *args, **kwargs):
            pass

        def read_sql(self, sql, geom_col="geometry"):
            return persisted.get("parcels", gpd.GeoDataFrame())

        def create_table_from_gdf(self, *args, **kwargs):
            table = args[1]
            temp_tables[table] = []

        def drop_table(self, table, schema="public"):
            temp_tables.pop(table, None)

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.PostGISPersister",
        DummyPersister,
    )

    def dummy_read_postgis(sql, engine, geom_col="geometry"):
        if "neighborhoods" in sql:
            return gpd.GeoDataFrame(
                {
                    "region_id": [1],
                    "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                },
                geometry="geometry",
                crs=settings.default_crs,
            )
        return gpd.GeoDataFrame(
            {"parcel_id": [1], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            geometry="geometry",
            crs=settings.default_crs,
        )

    monkeypatch.setattr(gpd, "read_postgis", dummy_read_postgis)

    # stitcher just concatenates GeoDataFrames stored in the temp table
    def dummy_stitch(self, table_name, layer_name, id_column, agg_rules, known_columns):
        dfs = temp_tables.get(table_name, [])
        if not dfs:
            return gpd.GeoDataFrame(geometry=[], crs=settings.default_crs)
        df = pd.concat(dfs, ignore_index=True)
        return gpd.GeoDataFrame(df, geometry="geometry", crs=settings.default_crs)

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.GeometryStitcher.stitch_from_table",
        dummy_stitch,
    )

    # make executor synchronous for predictable results
    class DummyExecutor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def map(self, func, *iterables):
            return map(func, *iterables)

    monkeypatch.setattr("concurrent.futures.ProcessPoolExecutor", DummyExecutor)

    # limit to a single layer
    monkeypatch.setattr(settings, "layers_to_process", ["parcels"])
    monkeypatch.setitem(settings.id_column_per_layer, "parcels", "parcel_id")

    # run the pipeline
    asyncio.run(run_pipeline(aoi_bbox=(0, 0, 1, 1), zoom=15))

    assert "parcels" in persisted
    assert len(persisted["parcels"]) == 1
    assert persisted["parcels"].iloc[0]["parcel_id"] == 1


def test_run_pipeline_with_save_as_temp(monkeypatch):
    """Pipeline writes parcels to a temp table and creates indexes."""
    import sqlalchemy
    # Patch inspect in orchestrator to always return a mock with has_table True
    class DummyInspector:
        def has_table(self, table_name, schema=None):
            return True
    monkeypatch.setattr("meshic_pipeline.pipeline_orchestrator.inspect", lambda engine: DummyInspector())
    monkeypatch.setattr("meshic_pipeline.pipeline_orchestrator.reset_temp_table", lambda *a, **kw: None)

    tile_bytes = mapbox_vector_tile.encode(
        {
            "name": "parcels",
            "features": [
                {
                    "geometry": Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                    "properties": {"parcel_id": 2},
                }
            ],
        },
        quantize_bounds=(0, 0, 1, 1),
        extents=4096,
    )

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.get_tile_coordinates_for_bounds",
        lambda bbox, zoom: [(15, 0, 0)],
    )

    class DummyDownloader:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            pass

        async def download_many(self, tiles):
            return {tiles[0]: tile_bytes}

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.AsyncTileDownloader",
        DummyDownloader,
    )

    persisted_tables: list[str] = []
    executed_sql: list[str] = []

    class DummyPersister:
        def __init__(self, *args, **kwargs):
            self.engine = None

        def write(
            self,
            gdf,
            layer_name,
            table,
            if_exists="append",
            id_column=None,
            schema="public",
            chunksize=5000,
            geometry_type=None,
        ):
            persisted_tables.append(table)

        def recreate_database(self):
            pass

        def execute(self, sql, *args, **kwargs):
            executed_sql.append(sql)

        def read_sql(self, sql, geom_col="geometry"):
            return gpd.GeoDataFrame()

        def create_table_from_gdf(self, *args, **kwargs):
            pass

        def drop_table(self, table, schema="public"):
            pass

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.PostGISPersister",
        DummyPersister,
    )

    def dummy_read_postgis(sql, engine, geom_col="geometry"):
        if "neighborhoods" in sql:
            return gpd.GeoDataFrame(
                {
                    "region_id": [1],
                    "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])],
                },
                geometry="geometry",
                crs=settings.default_crs,
            )
        return gpd.GeoDataFrame(
            {"parcel_id": [2], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            geometry="geometry",
            crs=settings.default_crs,
        )

    monkeypatch.setattr(gpd, "read_postgis", dummy_read_postgis)

    def dummy_stitch(self, table_name, layer_name, id_column, agg_rules, known_columns):
        return gpd.GeoDataFrame(
            {"parcel_id": [2], "geometry": [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]},
            geometry="geometry",
            crs=settings.default_crs,
        )

    monkeypatch.setattr(
        "meshic_pipeline.pipeline_orchestrator.GeometryStitcher.stitch_from_table",
        dummy_stitch,
    )

    class DummyExecutor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

        def map(self, func, *iterables):
            return map(func, *iterables)

    monkeypatch.setattr("concurrent.futures.ProcessPoolExecutor", DummyExecutor)

    monkeypatch.setattr(settings, "layers_to_process", ["parcels"])
    monkeypatch.setitem(settings.id_column_per_layer, "parcels", "parcel_id")

    asyncio.run(
        run_pipeline(aoi_bbox=(0, 0, 1, 1), zoom=15, save_as_temp="temp_parcels")
    )

    assert "temp_parcels" in persisted_tables
    assert any("CREATE INDEX" in sql and "temp_parcels" in sql for sql in executed_sql)
