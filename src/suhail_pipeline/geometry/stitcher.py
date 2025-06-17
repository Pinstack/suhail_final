from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import geopandas as gpd
import pandas as pd
from shapely.errors import GEOSException
from shapely.ops import snap

logger = logging.getLogger(__name__)


class GeometryStitcher:
    """Stitches geometries from multiple GeoDataFrames based on a common identifier."""

    def __init__(self, target_crs: str = "EPSG:4326"):
        """
        Initializes the stitcher with a specified target coordinate reference system.

        Args:
            target_crs: The CRS to project geometries to before stitching.
        """
        self.target_crs = target_crs

    def stitch_geometries(
        self,
        gdfs: List[gpd.GeoDataFrame],
        layer_name: str,
        id_column: Optional[str] = None,
        agg_rules: Optional[Dict[str, Any]] = None,
    ) -> gpd.GeoDataFrame:
        """
        Stitches geometries from a list of GeoDataFrames.

        Args:
            gdfs: A list of GeoDataFrames to stitch together.
            layer_name: The name of the layer being processed.
            id_column: The column to use for dissolving geometries. If None, all
                features are merged into a single geometry.
            agg_rules: A dictionary specifying how to aggregate attribute columns.

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
            # Gracefully handle potential empty results after dissolve
            try:
                # The dissolve operation can be slow on large, complex datasets
                stitched = combined.dissolve(by=id_column, aggfunc=final_agg_rules, as_index=False)
            except Exception as e:
                logger.error(
                    "Dissolve operation failed for layer '%s' with ID column '%s': %s",
                    layer_name,
                    id_column,
                    e,
                )
                return gpd.GeoDataFrame(geometry=[], crs=self.target_crs)
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

        # Apply buffer(0) to fix invalid polygons, a common issue after union/dissolve
        try:
            stitched.geometry = stitched.geometry.map(
                lambda p: p.buffer(0) if p.geom_type == "Polygon" else p
            )
        except Exception as e:
            logger.warning(
                "Applying buffer(0) failed for layer '%s': %s. Geometries may remain invalid.",
                layer_name,
                e,
            )

        return stitched.reset_index(drop=True)