import json
from shapely.geometry import shape
from shapely.ops import unary_union
import sys

# Usage: python validate_geojson_bounds.py <geojson_file>
filename = sys.argv[1] if len(sys.argv) > 1 else 'metro_lines_wgs84.geojson'

with open(filename) as f:
    fc = json.load(f)
    geoms = [shape(feat['geometry']) for feat in fc['features']]
    bounds = unary_union(geoms).bounds
    print('Bounds:', bounds)
    minx, miny, maxx, maxy = bounds
    # Riyadh rough extents
    if 46.5 < minx < 47.0 and 46.5 < maxx < 47.0 and 24.5 < miny < 25.0 and 24.5 < maxy < 25.0:
        print('All features are within expected Riyadh extents.')
    else:
        print('Warning: Some features are outside expected Riyadh extents!') 