import json
import re
from pathlib import Path

# Input and output paths
input_path = Path("sample_data/z10_tiles_with_parcels_urls.json")
output_path = Path("z15_tiles_to_scrape.json")

tile_re = re.compile(r"/(\d+)/(\d+)/(\d+)\\.vector\\.pbf|/(\d+)/(\d+)/(\d+)\.vector\.pbf", re.IGNORECASE)

z15_tiles = set()

with input_path.open() as f:
    urls = json.load(f)

for url in urls:
    m = tile_re.search(url)
    if not m:
        print(f"Could not parse tile from URL: {url}")
        continue
    # Support both possible match groups
    groups = [g for g in m.groups() if g is not None]
    if len(groups) == 3:
        z, x, y = map(int, groups)
    elif len(groups) == 6:
        z, x, y = map(int, groups[:3])
    else:
        print(f"Unexpected match groups for URL: {url}")
        continue
    if z != 10:
        print(f"Warning: Non-z10 tile in input: {url}")
    # Print debug info
    print(f"Expanding z10 tile: {url} -> z={z}, x={x}, y={y}")
    z15_tiles_for_this_z10 = []
    for dx in range(32):
        for dy in range(32):
            zx, zy = x * 32 + dx, y * 32 + dy
            z15_tiles.add((15, zx, zy))
            if len(z15_tiles_for_this_z10) < 5:
                z15_tiles_for_this_z10.append((15, zx, zy))
    print(f"  First 5 z15 tiles: {z15_tiles_for_this_z10}")

print(f"Total unique z15 tiles: {len(z15_tiles)}")

# Write to output as a sorted list of [z, x, y] lists
with output_path.open("w") as out:
    json.dump(sorted([list(t) for t in z15_tiles]), out)

print(f"Wrote expanded z15 tile list to {output_path}") 