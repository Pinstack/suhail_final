from __future__ import annotations

import logging
from typing import Optional, List
import uuid

import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)

# Add a canonical schema map for all layers
SCHEMA_MAP = {
    'parcels': {
        'parcel_objectid': 'int64',
        'geometry': 'geometry',
        'landuseagroup': 'string',
        'landuseadetailed': 'string',
        'subdivision_no': 'string',
        'transaction_price': 'float64',
        'zoning_id': 'int64',
        'neighborhood_id': 'int64',
        'block_no': 'string',
        'neighborhood_ar': 'string',
        'subdivision_id': 'int64',
        'price_of_meter': 'float64',
        'shape_area': 'float64',
        'zoning_color': 'string',
        'ruleid': 'string',
        'province_id': 'int64',
        'municipality_ar': 'string',
        'parcel_id': 'int64',
        'parcel_no': 'string',
        'created_at': 'datetime64[ns]',
        'updated_at': 'datetime64[ns]',
        'is_active': 'bool',
        'geometry_hash': 'string',
        'enriched_at': 'datetime64[ns]',
    },
    'parcels-centroids': {
        'parcel_no': 'string',
        'geometry': 'geometry',
        'transaction_date': 'datetime64[ns]',
        'transaction_price': 'float64',
        'price_of_meter': 'float64',
    },
    'neighborhoods': {
        'neighborhood_id': 'int64',
        'geometry': 'geometry',
        'neighborhood_name': 'string',
        'neighborhood_ar': 'string',
        'region_id': 'int64',
        'province_id': 'int64',
        'price_of_meter': 'float64',
        'shape_area': 'float64',
        'transaction_price': 'float64',
        'zoning_id': 'int64',
        'zoning_color': 'string',
        'geometry_hash': 'string',
    },
    'neighborhoods-centroids': {
        'neighborhood_id': 'int64',
        'geometry': 'geometry',
        'neighborhood_name': 'string',
    },
    'subdivisions': {
        'subdivision_id': 'int64',
        'geometry': 'geometry',
        'subdivision_no': 'string',
        'shape_area': 'float64',
        'transaction_price': 'float64',
        'price_of_meter': 'float64',
        'zoning_id': 'int64',
        'zoning_color': 'string',
        'province_id': 'int64',
    },
    'metro_lines': {
        'id': 'int64',
        'geometry': 'geometry',
        'track_color': 'string',
        'track_length': 'float64',
        'track_name': 'string',
    },
    'bus_lines': {
        'id': 'int64',
        'geometry': 'geometry',
        'route_name': 'string',
        'route_color': 'string',
        'route_length': 'float64',
        'route_type': 'string',
        'route_id': 'string',
    },
    'metro_stations': {
        'station_code': 'string',
        'geometry': 'geometry',
        'station_name': 'string',
        'line_id': 'int64',
        'location': 'string',
    },
    'riyadh_bus_stations': {
        'station_code': 'string',
        'geometry': 'geometry',
        'station_name': 'string',
        'route_id': 'string',
        'location': 'string',
    },
    'qi_population_metrics': {
        'grid_id': 'string',
        'population': 'int64',
        'geometry': 'geometry',
    },
    'qi_stripes': {
        'strip_id': 'string',
        'geometry': 'geometry',
        'stripe_value': 'float64',
        'stripe_type': 'string',
    },
}

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

    def _validate_and_cast_types(self, gdf: gpd.GeoDataFrame, layer_name: str) -> gpd.GeoDataFrame:
        """
        Validate and cast data types in GeoDataFrame before persistence, using the canonical schema for the layer.
        Additionally, cast any column containing 'date' in its name to datetime64[ns] for robustness.
        """
        schema = SCHEMA_MAP.get(layer_name)
        validated_gdf = gdf.copy()
        if schema:
            for col, dtype in schema.items():
                if col in validated_gdf.columns:
                    try:
                        if dtype in ('int64', 'Int64'):
                            # Accept int, float (if .is_integer()), or string (parseable as int/float and .is_integer())
                            def robust_int(val):
                                if val is None:
                                    return None
                                if isinstance(val, int):
                                    return val
                                if isinstance(val, float):
                                    return int(val) if val.is_integer() else None
                                if isinstance(val, str):
                                    try:
                                        float_val = float(val)
                                        return int(float_val) if float_val.is_integer() else None
                                    except Exception:
                                        return None
                                return None
                            validated_gdf[col] = validated_gdf[col].apply(lambda v: robust_int(v))
                        elif dtype == 'float64':
                            # Accept int, float, or string (parseable as float)
                            def robust_float(val):
                                if val is None:
                                    return None
                                if isinstance(val, (int, float)):
                                    return float(val)
                                if isinstance(val, str):
                                    try:
                                        return float(val)
                                    except Exception:
                                        return None
                                return None
                            validated_gdf[col] = validated_gdf[col].apply(lambda v: robust_float(v))
                        elif dtype == 'string':
                            validated_gdf[col] = validated_gdf[col].astype('string')
                        elif dtype == 'datetime64[ns]':
                            validated_gdf[col] = pd.to_datetime(validated_gdf[col], errors='coerce')
                        elif dtype == 'bool':
                            validated_gdf[col] = validated_gdf[col].astype('boolean')
                        # geometry handled by GeoPandas
                    except Exception as e:
                        logger.warning(f"Failed to cast {col} to {dtype}: {e}")
        # Always cast any column with 'date' in its name to datetime64[ns]
        for col in validated_gdf.columns:
            if 'date' in col and not pd.api.types.is_datetime64_any_dtype(validated_gdf[col]):
                try:
                    validated_gdf[col] = pd.to_datetime(validated_gdf[col], errors='coerce')
                except Exception as e:
                    logger.warning(f"Failed to force-cast {col} to datetime64[ns]: {e}")
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
    def _upsert(self, gdf: gpd.GeoDataFrame, table_name: str, id_column: str, schema: str, chunksize: int) -> None:
        """Performs an 'upsert' operation (INSERT ON CONFLICT) for a GeoDataFrame."""
        temp_table_name = f"temp_upsert_{table_name}_{str(uuid.uuid4())[:8]}"
        logger.info("Performing upsert on %s.%s using ID column '%s'", schema, table_name, id_column)
        try:
            # 1. Write the new data to a temporary table. This is more robust for large datasets.
            gdf.to_postgis(
                temp_table_name,
                self.engine,
                schema=schema,
                if_exists="replace",
                index=False,
                chunksize=chunksize,
            )
            # 2. Construct the ON CONFLICT query.
            cols = [f'"{c}"' for c in gdf.columns]
            cols_str = ", ".join(cols)
            update_cols = [f'"{c}" = EXCLUDED."{c}"' for c in gdf.columns if c != id_column]
            update_str = ", ".join(update_cols)
            id_col_quoted = f'"{id_column}"'
            sql = f'''
            INSERT INTO {schema}."{table_name}" ({cols_str})
            SELECT {cols_str} FROM {schema}."{temp_table_name}"
            ON CONFLICT ({id_col_quoted})
            DO UPDATE SET {update_str};
            '''
            with self.engine.begin() as conn:
                result = conn.execute(text(sql))
            logger.info("Upsert complete. Affected %d rows in %s.%s.", result.rowcount, schema, table_name)
        except Exception as e:
            logger.error("Upsert failed for table %s: %s", table_name, e)
            raise
        finally:
            self.drop_table(temp_table_name, schema)
            logger.debug("Dropped temporary upsert table: %s", temp_table_name)

    def write(self, gdf: gpd.GeoDataFrame, layer_name: str, table: str, if_exists: str = "append", id_column: str = None, schema: str = "public", chunksize: int = 5000) -> None:
        """
        Write a GeoDataFrame to the database, using schema-driven type enforcement. layer_name is now required.
        """
        # Enforce Point-only for centroids layers, metro_stations, and riyadh_bus_stations
        if layer_name.endswith('-centroids') or layer_name in ['metro_stations', 'riyadh_bus_stations']:
            non_point_count = (~gdf.geometry.type.isin(['Point'])).sum()
            if non_point_count > 0:
                logger.warning(f"Layer '{layer_name}': Dropping {non_point_count} non-Point geometries before DB write.")
            gdf = gdf[gdf.geometry.type == 'Point']
        validated_gdf = self._validate_and_cast_types(gdf, layer_name=layer_name)
        if if_exists == "append" and id_column:
            self._upsert(validated_gdf, table, id_column, schema, chunksize)
        else:
            validated_gdf.to_postgis(table, self.engine, schema=schema, if_exists=if_exists, index=False, chunksize=chunksize)
            logger.info("Persisted %d features to %s.%s using mode '%s'", len(validated_gdf), schema, table, if_exists)

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