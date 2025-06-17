import geopandas as gpd
import pandas as pd
import logging
from shapely.errors import GEOSException
from shapely.ops import snap
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

class GeometryStitcher:
    """Stitches geometries from multiple GeoDataFrames based on a common identifier."""

    def stitch_geometries(
        self,
        gdfs: List[gpd.GeoDataFrame],
        id_column: Optional[str],
        agg_rules: Optional[Dict[str, Any]] = None,
        target_crs: str = "EPSG:4326",
    ) -> gpd.GeoDataFrame:
        if not gdfs:
            return gpd.GeoDataFrame()

        # Reproject and validate CRS
        processed = []
        for gdf in gdfs:
            if gdf.crs != target_crs:
                gdf = gdf.to_crs(target_crs)
            processed.append(gdf)

        active = [g for g in processed if not g.empty]
        if not active:
            return gpd.GeoDataFrame(geometry=[], crs=target_crs)

        combined = pd.concat(active, ignore_index=True)
        if combined.empty:
            return gpd.GeoDataFrame(geometry=[], crs=target_crs)

        # Fix invalid geometries and snap coincident edges
        geom_col = combined.geometry.name
        try:
            combined[geom_col] = combined.geometry.apply(lambda g: snap(g, g, 1e-7))
            # Apply buffer(0) only for polygonal geometries to fix validity
            if combined.geom_type.isin(["Polygon", "MultiPolygon"]).all():
                combined[geom_col] = combined.geometry.buffer(0)
            combined = combined[~combined.geometry.is_empty]
        except GEOSException:
            pass

        # Default aggregation rules
        if agg_rules is None:
            agg_rules = {col: "first" for col in combined.columns if col not in [combined.geometry.name, id_column]}
        else:
            agg_rules = {k: v for k, v in agg_rules.items() if k in combined.columns and k not in [combined.geometry.name, id_column]}

        if id_column and id_column in combined.columns:
            stitched = combined.dissolve(by=id_column, aggfunc=agg_rules, as_index=False)
        else:
            # If no id_column, merge all
            stitched = gpd.GeoDataFrame(
                combined.geometry.unary_union, columns=["geometry"], crs=target_crs
            )
        return stitched.reset_index(drop=True) 