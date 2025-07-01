from __future__ import annotations

import geopandas as gpd
from shapely.errors import GEOSException
from shapely.ops import snap


def validate_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Fix validity issues (buffer(0) for polygons, snap for all)."""
    if gdf.empty:
        return gdf
    geom_col = gdf.geometry.name
    try:
        gdf[geom_col] = gdf.geometry.apply(lambda g: snap(g, g, 1e-7))
        if gdf.geom_type.isin(["Polygon", "MultiPolygon"]).all():
            gdf[geom_col] = gdf.buffer(0)
        gdf = gdf[~gdf.geometry.is_empty]
    except GEOSException:  # pragma: no cover
        pass
    return gdf.reset_index(drop=True) 