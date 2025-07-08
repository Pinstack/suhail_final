"""
Script Name: tile_discovery.py
Purpose: Discover z12 tiles with parcels, expand to z15 tiles, and output all z15 tile URLs as Z15_tiles.json. Only the z15 tile list is output; no other files are written.
Output:
  - Z15_tiles.json
Usage: python tile_discovery.py
"""
import json
import math
import asyncio
import aiohttp
from mapbox_vector_tile import decode
import os

REGIONS_PATH = 'data_raw/api/regions.json'
Z15_OUTPUT_PATH = 'data_raw/validation_reports/Z15_tiles.json'
ZOOM10 = 10
ZOOM12 = 12
ZOOM15 = 15
TILE_SERVER = 'https://tiles.suhail.ai/maps/{region}/{z}/{x}/{y}.vector.pbf'
MAX_RADIUS = 30  # tiles
CONCURRENCY = 20

# --- Step 1: Discover z12 tiles with parcels ---
def lonlat_to_tile(lon, lat, z):
    lat_rad = math.radians(lat)
    n = 2.0 ** z
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def has_parcels_with_geometry(tile_bytes):
    try:
        data = decode(tile_bytes)
        parcels = data.get('parcels', {})
        if isinstance(parcels, dict) and 'features' in parcels:
            features = parcels['features']
            if any(isinstance(f, dict) and 'geometry' in f and f['geometry'] for f in features):
                return True
    except Exception:
        pass
    return False

async def fetch_and_check_tile(url, session, sem):
    async with sem:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    tile_bytes = await resp.read()
                    if has_parcels_with_geometry(tile_bytes):
                        return url
        except Exception:
            pass
    return None

async def discover_z12_tiles():
    with open(REGIONS_PATH, encoding='utf-8') as f:
        regions_json = json.load(f)
    regions = regions_json['data']
    z12_tiles_with_parcels = set()
    sem = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession() as session:
        for region in regions:
            region_name = region['mapStyleUrl'].split('https://tiles.suhail.ai/')[1].strip('/') if 'mapStyleUrl' in region else region['key']
            centroid = region['centroid']
            cx, cy = lonlat_to_tile(centroid['x'], centroid['y'], ZOOM10)
            z10_tile_coords = [(cx + dx, cy + dy) for dx in range(-MAX_RADIUS, MAX_RADIUS + 1) for dy in range(-MAX_RADIUS, MAX_RADIUS + 1)]
            z10_urls = [TILE_SERVER.format(region=region_name, z=ZOOM10, x=x, y=y) for (x, y) in z10_tile_coords]
            z10_tasks = [fetch_and_check_tile(url, session, sem) for url in z10_urls]
            z10_results = await asyncio.gather(*z10_tasks)
            z10_positive_coords = [z10_tile_coords[i] for i, url in enumerate(z10_results) if url]
            # For each positive z10 tile, prepare all 16 z12 children URLs
            for (x10, y10) in z10_positive_coords:
                for dx in range(4):
                    for dy in range(4):
                        x12 = x10 * 4 + dx
                        y12 = y10 * 4 + dy
                        z12_tiles_with_parcels.add((region_name, x12, y12))
    # Output flat list of z12 tile URLs
    urls = [TILE_SERVER.format(region=region, z=ZOOM12, x=x, y=y) for (region, x, y) in z12_tiles_with_parcels]
    return urls

# --- Step 2: Expand z12 to z15 tiles and output ---
def expand_z12_to_z15_and_write(z12_urls):
    TILE_FACTOR = 8
    z15_urls = []
    import re
    for url in z12_urls:
        m = re.search(r'/maps/([^/]+)/([0-9]+)/([0-9]+)/([0-9]+)\.vector\.pbf', url.strip())
        if not m:
            continue
        region, z, x, y = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if z != ZOOM12:
            continue
        for dx in range(TILE_FACTOR):
            for dy in range(TILE_FACTOR):
                x15 = x * TILE_FACTOR + dx
                y15 = y * TILE_FACTOR + dy
                z15_urls.append(f"https://tiles.suhail.ai/maps/{region}/15/{x15}/{y15}.vector.pbf")
    os.makedirs(os.path.dirname(Z15_OUTPUT_PATH), exist_ok=True)
    with open(Z15_OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(z15_urls, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(z15_urls)} z15 tile URLs to {Z15_OUTPUT_PATH}")

# --- Main orchestration ---
async def main():
    z12_urls = await discover_z12_tiles()
    expand_z12_to_z15_and_write(z12_urls)

if __name__ == '__main__':
    asyncio.run(main()) 