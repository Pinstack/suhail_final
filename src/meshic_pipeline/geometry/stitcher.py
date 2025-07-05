from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from shapely.errors import GEOSException
from shapely.ops import snap
from tqdm import tqdm
import mercantile
from sqlalchemy import text

from ..persistence.postgis_persister import PostGISPersister

logger = logging.getLogger(__name__)


def _dissolve_group(
    group: Tuple[Any, pd.DataFrame],
    id_column: str,
    geom_column: str,
    agg_rules: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Worker function to dissolve a single group of geometries."""
    group_id, gdf = group
    try:
        # Perform the actual union of geometries for this group
        geom = gdf.unary_union
        if geom.is_empty:
            return None

        # Perform attribute aggregation
        props = gdf.iloc[0][list(agg_rules.keys())].to_dict()
        
        # Use the provided aggregation functions
        for col, rule in agg_rules.items():
            if rule == "sum":
                props[col] = gdf[col].sum()
            elif rule == "mean":
                props[col] = gdf[col].mean()
            # 'first' is implicitly handled by taking iloc[0]
            # Add other rules like 'max', 'min', etc. as needed

        return {id_column: group_id, "geometry": geom, **props}
    except Exception as e:
        logger.error("Failed to dissolve group %s: %s", group_id, e)
        return None


class GeometryStitcher:
    """Stitches geometries from multiple GeoDataFrames using a scalable, streaming approach with PostGIS."""

    def __init__(self, target_crs: str, persister: PostGISPersister):
        self.target_crs = target_crs
        self.persister = persister

    def _dissolve_in_postgis(
        self,
        temp_table_name: str,
        id_column: str,
        agg_rules: Dict[str, Any],
        layer_name: str,
    ) -> gpd.GeoDataFrame:
        """Offloads the dissolve operation to PostGIS using a pre-filled temporary table."""
        agg_cols = []
        for col, rule in agg_rules.items():
            # Use 'first' as a default aggregation for any specified column
            agg_cols.append(f'(array_agg("{col}"))[1] AS "{col}"')

        agg_sql = ", ".join(agg_cols)
        if agg_sql:
            agg_sql = ", " + agg_sql

        # Determine the geometry type to extract from ST_Union
        if layer_name.endswith("-centroids") or layer_name in ["metro_stations", "riyadh_bus_stations"]:
            extract_code = 1  # Point geometries
        elif layer_name in ["metro_lines", "bus_lines"]:
            extract_code = 2  # Line geometries
        else:
            extract_code = 3  # Polygon geometries

        sql = f"""
        SELECT
            "{id_column}",
            ST_CollectionExtract(ST_MakeValid(ST_Union(geometry)), {extract_code}) AS geometry{agg_sql}
        FROM "{temp_table_name}"
        GROUP BY "{id_column}"
        """

        logger.info("Executing PostGIS dissolve for layer '%s'...", layer_name)
        stitched_gdf = self.persister.read_sql(sql)
        logger.info("PostGIS dissolve complete. Read back %d features.", len(stitched_gdf))
        return stitched_gdf

    def stitch_geometries(
        self,
        gdfs: List[gpd.GeoDataFrame],
        layer_name: str,
        id_column: str | None,
        agg_rules: Dict[str, Any],
        tiles: List[Tuple[int, int, int]],
        known_columns: List[str],
    ) -> gpd.GeoDataFrame:
        temp_table_name = f"temp_{layer_name}_{str(uuid.uuid4())[:8]}"
        logger.info(
            "Stitching GeoDataFrames for layer '%s' using temp table '%s'.",
            layer_name, temp_table_name
        )
        
        # Create an empty GDF with the definitive schema to create the table
        # This is more reliable than using a sample from the generator.
        schema_gdf = gpd.GeoDataFrame(columns=known_columns)
        if 'geometry' not in schema_gdf.columns:
            schema_gdf['geometry'] = None # Ensure geometry column exists
        schema_gdf = schema_gdf.astype({'geometry': 'geometry'}) # Set the dtype

        try:
            self.persister.create_table_from_gdf(
                schema_gdf, temp_table_name, known_columns=known_columns
            )
            
            # Stream dataframes from the generator into the temporary table
            gdf_count = 0
            for gdf in gdfs:
                if gdf.empty:
                    continue

                # Reindex ensures all columns from the known_columns set are present
                gdf_standardized = gdf.reindex(columns=known_columns)
                # For centroids layers, ensure only Point geometries are written
                if layer_name.endswith('-centroids'):
                    non_point_count = (~gdf_standardized.geometry.type.isin(['Point'])).sum()
                    if non_point_count > 0:
                        logger.warning(f"Layer '{layer_name}': Dropping {non_point_count} non-Point geometries before DB write.")
                    gdf_standardized = gdf_standardized[gdf_standardized.geometry.type == 'Point']
                self.persister.write(gdf_standardized, layer_name, temp_table_name, if_exists="append")
                gdf_count += 1
            
            if gdf_count == 0:
                logger.warning("No non-empty GeoDataFrames were processed for layer '%s'.", layer_name)
                return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

            # Filter aggregation rules to only include columns that actually exist in the temp table.
            final_agg_rules = {col: rule for col, rule in agg_rules.items() if col in known_columns}
            dropped_rules = set(agg_rules.keys()) - set(final_agg_rules.keys())
            if dropped_rules:
                logger.warning(
                    "Layer '%s': Ignoring aggregation for non-existent columns: %s",
                    layer_name, ", ".join(sorted(list(dropped_rules)))
                )

            # Perform dissolve in PostGIS using the filtered, data-aware aggregation rules.
            final_gdf = self._dissolve_in_postgis(
                temp_table_name, id_column, final_agg_rules, layer_name
            )

        except Exception as e:
            logger.error(f"Stitching failed for layer {layer_name}: {e}")
            return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)
        finally:
            # 4. Clean up the temporary table
            self.persister.drop_table(temp_table_name)
            logger.info("Dropped temporary table: %s", temp_table_name)
            
        if final_gdf.empty:
            return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

        return final_gdf.reset_index(drop=True)
