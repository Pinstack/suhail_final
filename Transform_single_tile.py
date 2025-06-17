import argparse
import json
from typing import Any, Dict, List, Optional, Tuple, Union
from mapbox_vector_tile import decode
from pyproj import Transformer
from mercantile import xy_bounds

# Type aliases
Coords = Union[List[float], List[List[float]], List[List[List[float]]], List[List[List[List[float]]]]]
Feature = Dict[str, Any]


def get_tile_transformers(tile_bounds: Tuple[float, float, float, float], extent: int) -> Tuple[float, float, float, float]:
    mx_min, my_min, mx_max, my_max = tile_bounds
    scale_x = (mx_max - mx_min) / extent
    scale_y = (my_max - my_min) / extent
    return mx_min, my_min, scale_x, scale_y


def transform_coords(coords: List[List[float]], mx_min: float, my_min: float, scale_x: float, scale_y: float, to_wgs84) -> List[Tuple[float, float]]:
    return [to_wgs84(mx_min + x * scale_x, my_min + y * scale_y) for x, y in coords]


def recursive_transform(coords: Any, mx_min: float, my_min: float, scale_x: float, scale_y: float, to_wgs84) -> Any:
    """
    Recursively transform coordinates for Polygon/MultiPolygon.
    Handles nested lists of coordinates.
    """
    if isinstance(coords[0], (int, float)):
        return coords
    if isinstance(coords[0][0], (int, float)):
        return transform_coords(coords, mx_min, my_min, scale_x, scale_y, to_wgs84)
    return [recursive_transform(ring, mx_min, my_min, scale_x, scale_y, to_wgs84) for ring in coords]


def transform_point(coords: List[float], mx_min: float, my_min: float, scale_x: float, scale_y: float, to_wgs84) -> Tuple[float, float]:
    x, y = coords
    return to_wgs84(mx_min + x * scale_x, my_min + y * scale_y)


def transform_geometry(geom_type: str, coords: Any, mx_min: float, my_min: float, scale_x: float, scale_y: float, to_wgs84) -> Any:
    dispatch = {
        "Polygon": lambda c: recursive_transform(c, mx_min, my_min, scale_x, scale_y, to_wgs84),
        "MultiPolygon": lambda c: [recursive_transform(p, mx_min, my_min, scale_x, scale_y, to_wgs84) for p in c],
        "Point": lambda c: transform_point(c, mx_min, my_min, scale_x, scale_y, to_wgs84),
        "MultiPoint": lambda c: [transform_point(pt, mx_min, my_min, scale_x, scale_y, to_wgs84) for pt in c],
        "LineString": lambda c: transform_coords(c, mx_min, my_min, scale_x, scale_y, to_wgs84),
        "MultiLineString": lambda c: [transform_coords(line, mx_min, my_min, scale_x, scale_y, to_wgs84) for line in c],
    }
    return dispatch.get(geom_type, lambda c: None)(coords)


def extract_features(layer: Dict[str, Any], layer_name: Optional[str], mx_min: float, my_min: float, scale_x: float, scale_y: float, to_wgs84) -> List[Feature]:
features = []
    for feat in layer["features"]:
        geom_type = feat["geometry"]["type"]
        coords = feat["geometry"]["coordinates"]
        transformed = transform_geometry(geom_type, coords, mx_min, my_min, scale_x, scale_y, to_wgs84)
        if transformed is None:
            continue
        props = dict(feat["properties"])
        if layer_name is not None:
            props["_layer"] = layer_name
    features.append({
        "type": "Feature",
        "geometry": {
                "type": geom_type,
                "coordinates": transformed
        },
            "properties": props
        })
    return features


def main():
    parser = argparse.ArgumentParser(description="Transform and extract layers from a vector tile to WGS84 GeoJSON.")
    parser.add_argument('layer', nargs='?', default='all', help="Layer name to extract, or 'all' for all layers.")
    parser.add_argument('--output', '-o', default=None, help="Output GeoJSON file name.")
    parser.add_argument('--tile', default="20636_14069_15.vector.unzipped.pbf", help="Input vector tile filename.")
    parser.add_argument('--z', type=int, default=15, help="Tile zoom level.")
    parser.add_argument('--x', type=int, default=20636, help="Tile x index.")
    parser.add_argument('--y', type=int, default=14069, help="Tile y index.")
    parser.add_argument('--extent', type=int, default=4096, help="Tile extent (default 4096).")
    args = parser.parse_args()

    tile_bounds = xy_bounds(args.x, args.y, args.z)
    mx_min, my_min, scale_x, scale_y = get_tile_transformers(tile_bounds, args.extent)
    to_wgs84 = Transformer.from_crs(3857, 4326, always_xy=True).transform

    with open(args.tile, "rb") as f:
        data = decode(f.read())

    features = []
    if args.layer == 'all':
        for layer_name, layer in data.items():
            features.extend(extract_features(layer, layer_name, mx_min, my_min, scale_x, scale_y, to_wgs84))
        out_file = args.output or "all_layers_wgs84.geojson"
    else:
        if args.layer not in data:
            raise ValueError(f"Layer '{args.layer}' not found in tile.")
        features = extract_features(data[args.layer], None, mx_min, my_min, scale_x, scale_y, to_wgs84)
        out_file = args.output or f"{args.layer}_wgs84.geojson"

geojson = {
    "type": "FeatureCollection",
    "features": features
}

    with open(out_file, "w") as f:
    json.dump(geojson, f)
    print(f"Wrote {len(features)} features to {out_file}")


if __name__ == "__main__":
    main()