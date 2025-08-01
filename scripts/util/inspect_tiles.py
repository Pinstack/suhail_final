import os
import glob
import re
from meshic_pipeline.decoder.mvt_decoder import MVTDecoder

from collections import defaultdict

tile_dir = "temp_tiles"
tiles = glob.glob(os.path.join(tile_dir, "*.pbf"))
decoder = MVTDecoder()
summary = {}
layer_columns = defaultdict(set)
unique_zoning_ids = set()

for tile in tiles:
    m = re.match(r'.*([0-9]+)_([0-9]+)_([0-9]+)\.pbf', tile)
    if not m:
        continue
    z, x, y = map(int, m.groups())
    with open(tile, 'rb') as f:
        data = f.read()
    decoded = decoder.decode_bytes(data, z, x, y)
    print(f"{os.path.basename(tile)}: {list(decoded.keys())}")
    for layer, features in decoded.items():
        summary.setdefault(layer, 0)
        summary[layer] += len(features)
        for feat in features:
            layer_columns[layer].update(feat.keys())
            if layer == 'parcels' and 'zoning_id' in feat:
                unique_zoning_ids.add(feat['zoning_id'])

print("\nLayer summary:")
for layer, count in summary.items():
    print(f"{layer}: {count} features")

print("\nLayer columns:")
for layer, cols in layer_columns.items():
    print(f"{layer}: {sorted(cols)}")

# Print all unique zoning_id values found in parcels
print("\nUnique zoning_id values in parcels layer:")
for val in sorted(unique_zoning_ids, key=lambda x: (str(type(x)), str(x))):
    print(f"  - {repr(val)} ({type(val).__name__})")
