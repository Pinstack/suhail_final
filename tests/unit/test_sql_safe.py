import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from sqlalchemy import create_engine, inspect, text
import pytest

from meshic_pipeline.persistence.postgis_persister import PostGISPersister


class SQLitePersister(PostGISPersister):
    def __init__(self):
        self.database_url = "sqlite:///:memory:"
        self.engine = create_engine(self.database_url, future=True)

    def drop_table(self, table: str, schema: str = "main"):
        with self.engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))

    def create_table_from_gdf(self, gdf, table_name, schema="main", known_columns=None, geometry_type=None):
        if not known_columns:
            df = gdf.iloc[0:0]
            df.to_sql(table_name, self.engine, if_exists="replace", index=False)
            return
        column_defs = []
        for col in known_columns:
            q_col = col.replace('"', '""')
            if col.lower() == "geometry":
                column_defs.append(f'"{q_col}" TEXT')
            else:
                column_defs.append(f'"{q_col}" TEXT')
        create_sql = f'CREATE TABLE "{table_name}" ({", ".join(column_defs)})'
        with self.engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}"'))
            conn.execute(text(create_sql))


def to_sqlite(self, table, engine, schema=None, if_exists="append", index=False, chunksize=None, dtype=None):
    df = pd.DataFrame(self)
    if "geometry" in df.columns:
        df["geometry"] = df["geometry"].apply(lambda g: g.wkt if g is not None else None)
    name = table if schema is None else f"{schema}.{table}"
    df.to_sql(name, engine, if_exists=if_exists, index=index)


@pytest.fixture
def persister(monkeypatch):
    p = SQLitePersister()
    monkeypatch.setattr(gpd.GeoDataFrame, "to_postgis", to_sqlite)
    return p


def test_create_table_from_gdf_unusual_names(persister):
    gdf = gpd.GeoDataFrame(columns=["id", "weird column"], geometry=[])  # empty schema
    persister.create_table_from_gdf(gdf, "weird-table", schema="main", known_columns=["id", "weird column"])
    inspector = inspect(persister.engine)
    assert inspector.has_table("weird-table")
    cols = [c["name"] for c in inspector.get_columns("weird-table")]
    assert "weird column" in cols


def test_upsert_rejects_injection(persister):
    gdf = gpd.GeoDataFrame({"id": [1]}, geometry=[Point(0, 0)])
    with pytest.raises(ValueError):
        persister._upsert(gdf, "bad;drop", "id", "main", chunksize=10)


def test_upsert_with_unusual_names(persister, monkeypatch):
    gdf = gpd.GeoDataFrame({"id": [1], "weird column": [5], "geometry": [Point(0, 0)]}, geometry="geometry")
    persister.create_table_from_gdf(gdf.iloc[0:0], "weird-table", schema="main", known_columns=list(gdf.columns))

    calls: list[str] = []

    class DummyConn:
        def __enter__(self, *a):
            return self
        def __exit__(self, exc_type, exc, tb):
            pass
        def execute(self, stmt):
            calls.append(str(stmt))
            class R:
                rowcount = 1
            return R()

    persister.engine.begin = lambda: DummyConn()
    monkeypatch.setattr(gpd.GeoDataFrame, "to_postgis", lambda *a, **k: None)
    persister._upsert(gdf, "weird-table", "id", "main", chunksize=10)

    assert any('"weird column"' in c for c in calls)
