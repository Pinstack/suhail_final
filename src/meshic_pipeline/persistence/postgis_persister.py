from __future__ import annotations

import logging
from typing import Optional

import geopandas as gpd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class PostGISPersister:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Engine = create_engine(database_url, future=True)
        # Ensure PostGIS extension is available before any writes; this is idempotent
        with self.engine.connect() as conn:
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()  # Make sure the extension creation is committed
            except Exception as exc:
                logger.error("Failed to ensure PostGIS extension: %s", exc)
                raise

    # ------------------------------------------------------------------
    def recreate_database(self) -> None:
        """Drop and recreate the target database (requires superuser)."""
        url = self.engine.url
        # Connect to postgres maintenance DB
        admin_url = url.set(database="postgres")
        admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
        db_name = url.database
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            conn.execute(text(f"CREATE DATABASE {db_name} TEMPLATE template0"))
        # Recreate extension in the fresh database
        # Dispose any existing pooled connections tied to the old database
        self.engine.dispose()
        self.engine = create_engine(self.database_url, future=True)
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
        logger.info("Database %s recreated", db_name)

    # ------------------------------------------------------------------
    def write(self, gdf: gpd.GeoDataFrame, table: str, schema: str = "public", if_exists: str = "replace", chunksize: int = 5000) -> None:
        if gdf.empty:
            logger.warning("%s: GeoDataFrame empty, skipping write", table)
            return
        gdf.to_postgis(table, self.engine, schema=schema, if_exists=if_exists, index=False, chunksize=chunksize)
        logger.info("Persisted %d features to %s.%s", len(gdf), schema, table)

    def read_sql(self, sql: str, geom_col: str = "geometry") -> gpd.GeoDataFrame:
        """Executes a SQL query and returns the result as a GeoDataFrame."""
        return gpd.read_postgis(sql, self.engine, geom_col=geom_col)

    # Convenience -------------------------------------------------------
    def drop_table(self, table: str, schema: str = "public") -> None:
        with self.engine.begin() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table}" CASCADE'))

    def execute(self, sql: str) -> None:
        """Executes a raw SQL statement."""
        with self.engine.begin() as conn:
            conn.execute(text(sql)) 