import os
import requests

Z = 15
CENTER_X = 20636
CENTER_Y = 14069
TILE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"

# 2x2 grid: (x, y) in [CENTER_X, CENTER_X+1] x [CENTER_Y, CENTER_Y+1]
def download_tile(z: int, x: int, y: int):
    url = TILE_URL.format(z=z, x=x, y=y)
    out_filename = f"{z}_{x}_{y}.pbf"
    if os.path.exists(out_filename):
        print(f"{out_filename} already exists, skipping.")
        return
    print(f"Downloading {url} ...")
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(out_filename, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Saved {out_filename}")

if __name__ == "__main__":
    for dx in range(2):
        for dy in range(2):
            x = CENTER_X + dx
            y = CENTER_Y + dy
            download_tile(Z, x, y) 