from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import mapbox_vector_tile
import mercantile
from shapely.geometry import shape, mapping  # type: ignore
from shapely.geometry.base import BaseGeometry
from pyproj import Transformer


class MVTDecoder:
    """Decode raw Mapbox Vector Tile bytes and convert pixel coords → EPSG:4326 geometries."""

    def _transform_geometry(
        self,
        geom: dict[str, Any],
        mx_min: float,
        my_min: float,
        scale_x: float,
        scale_y: float,
        to_wgs84,
    ) -> BaseGeometry:
        """Recursively scale & project coordinate tuples and return Shapely geom."""

        g_type = geom["type"]
        coords = geom["coordinates"]

        def tx_pt(pt: Tuple[float, float]):
            x, y = pt
            return to_wgs84(mx_min + x * scale_x, my_min + y * scale_y)

        def recurse(obj):
            if not obj:
                return obj
            if isinstance(obj[0], (int, float)):
                # point tuple
                return tx_pt(obj)  # type: ignore[arg-type]
            return [recurse(o) for o in obj]

        new_coords = recurse(coords)
        return shape({"type": g_type, "coordinates": new_coords})

    def decode_bytes(
        self,
        tile_data: bytes,
        *,
        z: int,
        x: int,
        y: int,
        layers: Sequence[str] | None = None,
    ) -> Dict[str, List[dict[str, Any]]]:
        """Decode a single tile and return dict[layer] -> list of feature dicts with Shapely geometry."""

        raw = mapbox_vector_tile.decode(tile_data)
        tile_bounds = mercantile.xy_bounds(x, y, z)
        mx_min, my_min, mx_max, my_max = tile_bounds
        # extent from any layer (all share)
        some_layer = next(iter(raw.values()))
        extent = some_layer.get("extent", 4096)
        scale_x = (mx_max - mx_min) / extent
        scale_y = (my_max - my_min) / extent

        to_wgs84 = Transformer.from_crs(3857, 4326, always_xy=True).transform

        out: Dict[str, List[dict[str, Any]]] = {}
        for layer_name, layer_dict in raw.items():
            if layers is not None and layer_name not in layers:
                continue
            feats_out: List[dict[str, Any]] = []
            for feat in layer_dict.get("features", []):
                geom = self._transform_geometry(
                    feat["geometry"], mx_min, my_min, scale_x, scale_y, to_wgs84
                )
                if geom.is_empty:
                    continue
                props = dict(feat["properties"])
                feats_out.append({**props, "geometry": geom})
            out[layer_name] = feats_out
        return out 