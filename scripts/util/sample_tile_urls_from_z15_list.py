import json
import random
import requests

# Path to the z15 tile list
z15_path = "z15_tiles_to_scrape.json"

with open(z15_path) as f:
    tiles = json.load(f)

sampled = random.sample(tiles, min(10, len(tiles)))

# For demonstration, default to Riyadh. In production, you would map z15 tiles to their region.
TILE_URL_TEMPLATE = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"

for z, x, y in sampled:
    url = TILE_URL_TEMPLATE.format(z=z, x=x, y=y)
    try:
        resp = requests.head(url, timeout=10)
        print(f"{url} -> {resp.status_code}")
    except Exception as e:
        print(f"{url} -> ERROR: {e}") 