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
    """Stitches geometries from multiple GeoDataFrames using PostGIS for scalability."""

    def __init__(self, target_crs: str, persister: PostGISPersister):
        """
        Initializes the stitcher with a CRS and a PostGIS persister.
        """
        self.target_crs = target_crs
        self.persister = persister

    def _dissolve_in_postgis(
        self,
        gdf: gpd.GeoDataFrame,
        id_column: str,
        agg_rules: Dict[str, Any],
        layer_name: str,
    ) -> gpd.GeoDataFrame:
        """Offloads the dissolve operation to PostGIS."""
        temp_table_name = f"temp_{layer_name}_{uuid.uuid4().hex[:8]}"
        logger.info("Using temporary table: %s", temp_table_name)
        
        try:
            # 1. Write raw data to a temporary table
            self.persister.write(gdf, temp_table_name, if_exists="replace")

            # 2. Construct the SQL for dissolving
            agg_cols = []
            for col, rule in agg_rules.items():
                if rule == "first":
                    # Use the correct PostgreSQL syntax for 'first'
                    agg_cols.append(f'(array_agg("{col}"))[1] AS "{col}"')
                # Add other rules like SUM, AVG etc. as needed
                # e.g., elif rule == "sum": agg_cols.append(f'SUM("{col}") AS "{col}"')
            
            agg_sql = ", ".join(agg_cols)
            
            # Ensure there's a comma if we have aggregations
            if agg_sql:
                agg_sql = ", " + agg_sql

            sql = f"""
            SELECT
                "{id_column}",
                ST_CollectionExtract(ST_Union(geometry), 3) AS geometry{agg_sql}
            FROM "{temp_table_name}"
            GROUP BY "{id_column}"
            """
            
            # 3. Execute the dissolve and read back the result
            logger.info("Executing PostGIS dissolve for layer '%s'...", layer_name)
            stitched_gdf = self.persister.read_sql(sql)
            logger.info("PostGIS dissolve complete. Read back %d features.", len(stitched_gdf))
            return stitched_gdf
            
        finally:
            # 4. Clean up the temporary table
            self.persister.drop_table(temp_table_name)
            logger.info("Dropped temporary table: %s", temp_table_name)

    def stitch_geometries(
        self,
        gdfs: List[gpd.GeoDataFrame],
        layer_name: str,
        id_column: Optional[str] = None,
        agg_rules: Optional[Dict[str, Any]] = None,
        tiles: Optional[List[Tuple[int, int, int]]] = None,
    ) -> gpd.GeoDataFrame:
        """
        Stitches geometries from a list of GeoDataFrames.

        Args:
            gdfs: A list of GeoDataFrames to stitch together.
            layer_name: The name of the layer being processed.
            id_column: The column to use for dissolving geometries. If None, all
                features are merged into a single geometry.
            agg_rules: A dictionary specifying how to aggregate attribute columns.
            tiles: A list of tile coordinates (z, x, y) used to generate a
                snapping grid, which is much more efficient.

        Returns:
            A GeoDataFrame with stitched geometries.
        """
        if not gdfs:
            logger.warning("Received an empty list of GeoDataFrames for layer '%s'.", layer_name)
            return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

        logger.info(
            "Stitching %d GeoDataFrames for layer '%s'. ID column: %s.",
            len(gdfs),
            layer_name,
            id_column,
        )

        try:
            # Concatenate all GeoDataFrames, ignoring empty ones
            combined = pd.concat([gdf for gdf in gdfs if not gdf.empty], ignore_index=True)
            if combined.empty:
                logger.warning("Concatenated GeoDataFrame is empty for layer '%s'.", layer_name)
                return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

            # Ensure it's a GeoDataFrame with the correct CRS
            combined = gpd.GeoDataFrame(combined, crs=self.target_crs)
            geom_col = combined.geometry.name

        except Exception as e:
            logger.error(
                "Failed to concatenate GeoDataFrames for layer '%s': %s", layer_name, e
            )
            return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

        # Reproject to the target CRS if not already set
        if combined.crs != self.target_crs:
            combined = combined.to_crs(self.target_crs)

        # Prepare aggregation rules
        final_agg_rules = {}
        if agg_rules:
            # Filter provided rules to only include columns that actually exist
            final_agg_rules = {
                k: v
                for k, v in agg_rules.items()
                if k in combined.columns and k not in [geom_col, id_column]
            }

        # If no valid aggregation rules are left, default to taking the first value
        # for all available non-geometry, non-ID columns.
        if not final_agg_rules:
            final_agg_rules = {
                c: "first"
                for c in combined.columns
                if c not in [geom_col, id_column]
            }

        logger.info(
            "Layer '%s' | Columns: %s", layer_name, combined.columns.tolist()
        )
        logger.info(
            "Layer '%s' | Final Aggregation Rules: %s", layer_name, final_agg_rules
        )

        # Dissolve based on the ID column
        if id_column and id_column in combined.columns:
            logger.debug("Offloading dissolve to PostGIS for layer: %s", layer_name)
            stitched = self._dissolve_in_postgis(
                combined, id_column, final_agg_rules, layer_name
            )
        else:
            # No ID column provided, so merge all geometries into one
            union_geom = combined.unary_union
            if union_geom.is_empty:
                logger.warning(
                    "Union of geometries for layer '%s' is empty. No ID column was provided.",
                    layer_name,
                )
                return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)
            stitched = gpd.GeoDataFrame(
                {"geometry": [union_geom]}, crs=self.target_crs
            )

        # Final cleanup and validation
        if stitched.empty:
            logger.warning(
                "Stitching result for layer '%s' is empty after dissolve/union.",
                layer_name,
            )
            return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)

        # Apply buffer(0) to fix invalid polygons using a vectorized approach
        try:
            is_polygon = stitched.geometry.geom_type == "Polygon"
            # Apply buffer(0) to all polygons in a single, vectorized operation
            if is_polygon.any():
                logger.debug("Layer '%s': Applying vectorized buffer(0) to %d polygons.", layer_name, is_polygon.sum())
                stitched.loc[is_polygon, "geometry"] = stitched.loc[is_polygon, "geometry"].buffer(0)
        except Exception as e:
            logger.warning(
                "Applying buffer(0) failed for layer '%s': %s. Geometries may remain invalid.",
                layer_name,
                e,
            )

        return stitched.reset_index(drop=True)