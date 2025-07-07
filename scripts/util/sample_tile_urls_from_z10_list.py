import json
import random
import requests

z10_path = "sample_data/z10_tiles_with_parcels_urls.json"

with open(z10_path) as f:
    urls = json.load(f)

sampled = random.sample(urls, min(10, len(urls)))

for url in sampled:
    try:
        resp = requests.head(url, timeout=10)
        print(f"{url} -> {resp.status_code}")
    except Exception as e:
        print(f"{url} -> ERROR: {e}") 