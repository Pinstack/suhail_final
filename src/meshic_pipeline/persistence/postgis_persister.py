from __future__ import annotations

import logging
from typing import Optional, List

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class PostGISPersister:
    # Define expected integer ID fields for validation
    INTEGER_ID_FIELDS = {
        'parcel_id', 'zoning_id', 'subdivision_id', 'neighborhood_id', 
        'province_id', 'municipality_id', 'region_id', 'parcel_objectid'
    }
    
    # Define expected numeric/float fields for proper schema creation
    NUMERIC_FIELDS = {
        'shape_area', 'transaction_price', 'price_of_meter', 'area', 'price'
    }
    
    # Define string/varchar fields that should remain as large IDs (but as strings)
    STRING_ID_FIELDS = {
        'parcel_no', 'subdivision_no', 'block_no', 'cluster_id'
    }

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

    def _validate_and_cast_types(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Validate and cast data types in GeoDataFrame before persistence.
        
        Args:
            gdf: Input GeoDataFrame
            
        Returns:
            GeoDataFrame with validated and cast types
        """
        if gdf.empty:
            return gdf
        
        # Create a copy to avoid modifying the original
        validated_gdf = gdf.copy()
        
        for column in validated_gdf.columns:
            if column == 'geometry':
                continue
                
            if column in self.INTEGER_ID_FIELDS:
                # Cast integer ID fields
                try:
                    # Convert to numeric first, handling mixed types
                    numeric_series = pd.to_numeric(
                        validated_gdf[column], 
                        errors='coerce'
                    )
                    
                    # Round fractional values to nearest integer before conversion
                    rounded_series = numeric_series.round()
                    
                    # Convert to nullable integer type to handle NaN values properly
                    validated_gdf[column] = rounded_series.astype('Int64')
                    
                    # Check for any conversion failures
                    null_count = validated_gdf[column].isna().sum()
                    original_null_count = gdf[column].isna().sum()
                    
                    if null_count > original_null_count:
                        logger.warning(
                            f"Column {column}: {null_count - original_null_count} values "
                            f"could not be converted to integers and were set to null"
                        )
                        
                    # Check for rounding that occurred
                    if not numeric_series.isna().all():
                        rounded_values = (numeric_series != rounded_series).sum()
                        if rounded_values > 0:
                            logger.info(
                                f"Column {column}: {rounded_values} fractional values were rounded to integers"
                            )
                        
                except Exception as e:
                    logger.warning(f"Failed to cast {column} to integer: {e}")
                    
            elif column in self.NUMERIC_FIELDS:
                # Cast numeric fields to float
                try:
                    # Convert to numeric, handling mixed types
                    numeric_series = pd.to_numeric(
                        validated_gdf[column], 
                        errors='coerce'
                    )
                    
                    # Use float64 type for numeric precision
                    validated_gdf[column] = numeric_series.astype('float64')
                    
                    # Check for conversion failures
                    null_count = validated_gdf[column].isna().sum()
                    original_null_count = gdf[column].isna().sum()
                    
                    if null_count > original_null_count:
                        logger.warning(
                            f"Column {column}: {null_count - original_null_count} values "
                            f"could not be converted to numeric and were set to null"
                        )
                        
                except Exception as e:
                    logger.warning(f"Failed to cast {column} to numeric: {e}")
                    
            elif column in self.STRING_ID_FIELDS:
                # Ensure string ID fields are properly converted to string
                try:
                    validated_gdf[column] = validated_gdf[column].astype('string')
                except Exception as e:
                    logger.warning(f"Failed to cast {column} to string: {e}")
        
        return validated_gdf

    def create_table_from_gdf(
        self,
        gdf: gpd.GeoDataFrame,
        table_name: str,
        schema: str = "public",
        known_columns: List[str] | None = None,
    ):
        """
        Creates an empty PostGIS table with a specified schema.
        If known_columns is provided, it uses that to build the schema.
        Otherwise, it infers the schema from the sample GeoDataFrame.
        """
        if not known_columns:
            # Fallback to original behavior if no explicit schema is given
            try:
                empty_gdf = gdf.iloc[0:0]
                empty_gdf.to_postgis(
                    table_name,
                    self.engine,
                    schema=schema,
                    if_exists="replace",
                    index=False,
                )
                logger.info("Successfully created table %s.%s from GDF schema", schema, table_name)
            except Exception as e:
                logger.error("Failed to create table %s.%s from GDF: %s", schema, table_name, e)
                raise
            return

        # --- Build CREATE TABLE statement from known_columns ---
        column_defs = []
        for col_name in known_columns:
            if col_name.lower() == "geometry":
                # Use a generic geometry type; PostGIS will adapt
                column_defs.append(f'"{col_name}" GEOMETRY(GEOMETRY, 4326)')
            elif col_name in self.INTEGER_ID_FIELDS:
                # Use BIGINT for integer ID fields
                column_defs.append(f'"{col_name}" BIGINT')
            elif col_name in self.NUMERIC_FIELDS:
                # Use DOUBLE PRECISION for numeric fields (price, area, etc.)
                column_defs.append(f'"{col_name}" DOUBLE PRECISION')
            elif col_name in self.STRING_ID_FIELDS:
                # Use VARCHAR for string-based identifiers
                column_defs.append(f'"{col_name}" VARCHAR(50)')
            else:
                # Default to TEXT for other fields (names, descriptions, etc.)
                column_defs.append(f'"{col_name}" TEXT')

        create_sql = f'CREATE TABLE {schema}."{table_name}" ({", ".join(column_defs)});'
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(f'DROP TABLE IF EXISTS {schema}."{table_name}" CASCADE'))
                conn.execute(text(create_sql))
                conn.commit()
            logger.info("Successfully created table %s.%s from known columns", schema, table_name)
        except Exception as e:
            logger.error("Failed to create table %s.%s with SQL: %s", schema, table_name, e)
            raise

    # ------------------------------------------------------------------
    def recreate_database(self) -> None:
        """Drop and recreate the target database (requires superuser)."""
        url = self.engine.url
        # Dispose any existing pooled connections tied to the old database before dropping
        self.engine.dispose()
        # Connect to postgres maintenance DB
        admin_url = url.set(database="postgres")
        admin_engine = create_engine(admin_url, future=True, isolation_level="AUTOCOMMIT")
        db_name = url.database
        with admin_engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS {db_name}"))
            conn.execute(text(f"CREATE DATABASE {db_name} TEMPLATE template0"))
        # Recreate engine for the fresh database and ensure PostGIS extension
        self.engine = create_engine(self.database_url, future=True)
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
        logger.info("Database %s recreated", db_name)

    # ------------------------------------------------------------------
    def write(self, gdf: gpd.GeoDataFrame, table: str, schema: str = "public", if_exists: str = "append", chunksize: int = 5000) -> None:
        if gdf.empty:
            logger.warning("%s: GeoDataFrame empty, skipping write", table)
            return
        
        # Validate and cast types before writing
        validated_gdf = self._validate_and_cast_types(gdf)
        
        validated_gdf.to_postgis(table, self.engine, schema=schema, if_exists=if_exists, index=False, chunksize=chunksize)
        logger.info("Persisted %d features to %s.%s", len(validated_gdf), schema, table)

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