import asyncio
import pandas as pd
import geopandas as gpd
import pytest
from shapely.geometry import Polygon
import mapbox_vector_tile

from meshic_pipeline.pipeline_orchestrator import run_pipeline
from meshic_pipeline.config import settings

# Integration test that exercises the pipeline orchestration with mocked
# downloader and database persistence.


def test_run_pipeline_with_mocks(monkeypatch):
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
        ):
            if table.startswith("temp"):
                temp_tables.setdefault(table, []).append(gdf)
            else:
                persisted[layer_name] = gdf

        def recreate_database(self):
            pass

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

    # run the pipeline
    asyncio.run(run_pipeline(aoi_bbox=(0, 0, 1, 1), zoom=15))

    assert "parcels" in persisted
    assert len(persisted["parcels"]) == 1
    assert persisted["parcels"].iloc[0]["parcel_id"] == 1
