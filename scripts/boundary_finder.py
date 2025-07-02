import collections
import logging

import httpx
import mercantile
from tqdm import tqdm

# --- Configuration ---
LOG_LEVEL = logging.INFO
BASE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
Z = 5 # The lowest zoom level known to contain meaningful data

# A generous bounding box for the entire Riyadh Province
# Format: (west, south, east, north)
RIYADH_PROVINCE_BBOX = (43.5, 22.0, 48.0, 27.0)

# Use a standard user-agent, just in case the server checks for it.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

# --- Existing AOI from pipeline_config.yaml ---
EXISTING_GRID_CENTER_X = 20636
EXISTING_GRID_CENTER_Y = 14069
EXISTING_GRID_W = 52
EXISTING_GRID_H = 52
EXISTING_GRID_ZOOM = 15

# --- Setup ---
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_bbox_for_grid(center_x, center_y, width, height, zoom):
    """Calculates the geographic bounding box for a tile grid."""
    start_x = center_x - width // 2
    start_y = center_y - height // 2
    end_x = start_x + width -1
    end_y = start_y + height -1
    
    # Get bounds of the top-left and bottom-right tiles
    ul_bounds = mercantile.bounds(start_x, start_y, zoom)
    lr_bounds = mercantile.bounds(end_x, end_y, zoom)
    
    # Combine them to get the full extent
    west = ul_bounds.west
    south = lr_bounds.south
    east = lr_bounds.east
    north = ul_bounds.north
    
    return west, south, east, north


def check_tile_exists(client: httpx.Client, z: int, x: int, y: int) -> bool:
    """
    Checks if a tile at a given z, x, y coordinate exists and contains data.
    """
    url = BASE_URL.format(z=z, x=x, y=y)
    try:
        response = client.get(url, timeout=20)
        # Success and the tile has a meaningful size (not just a placeholder)
        if response.status_code == 200 and response.headers.get('Content-Length', '0') != '156':
            return True
        elif response.status_code != 404:
            logging.warning(f"Tile {z}/{x}/{y} returned status {response.status_code}")
    except httpx.RequestError as e:
        logging.error(f"Request for tile {z}/{x}/{y} failed: {e}")
    return False


def main():
    """
    Finds all tiles with data and compares the resulting bounding box
    with the one defined by the grid in the pipeline config.
    """
    print(f"--- Starting exhaustive search for tiles at Z={Z} ---")
    
    # 1. Generate all tiles for the region
    tiles_to_check = list(mercantile.tiles(*RIYADH_PROVINCE_BBOX, zooms=[Z]))
    print(f"Generated {len(tiles_to_check)} tiles to check for the Riyadh region.")

    valid_tiles = []
    with httpx.Client(headers=HEADERS) as client:
        with tqdm(total=len(tiles_to_check), desc=f"Checking Z{Z} tiles") as pbar:
            for tile in tiles_to_check:
                if check_tile_exists(client, tile.z, tile.x, tile.y):
                    valid_tiles.append(tile)
                pbar.update(1)

    if not valid_tiles:
        print("\n--- No valid data tiles were found in the specified region. ---")
        return

    # 4. Find the min/max x and y of the valid tiles
    min_x = min(t.x for t in valid_tiles)
    max_x = max(t.x for t in valid_tiles)
    min_y = min(t.y for t in valid_tiles)
    max_y = max(t.y for t in valid_tiles)

    # 5. Convert tile bounds to a geographic bounding box
    west, south, _, _ = mercantile.bounds(min_x, max_y, Z)
    _, _, east, north = mercantile.bounds(max_x, min_y, Z)
    discovered_bbox = (west, south, east, north)

    print("\n--- Comparison of Findings ---")
    
    # Calculate the bounding box of the existing grid
    existing_bbox = get_bbox_for_grid(
        EXISTING_GRID_CENTER_X, 
        EXISTING_GRID_CENTER_Y, 
        EXISTING_GRID_W, 
        EXISTING_GRID_H, 
        EXISTING_GRID_ZOOM
    )
    
    print("\n1. Existing AOI (from pipeline_config.yaml grid):")
    print(f"   - Grid: {EXISTING_GRID_W}x{EXISTING_GRID_H} tiles at z{EXISTING_GRID_ZOOM}")
    print(f"   - Bounding Box: {existing_bbox}")

    print("\n2. Discovered AOI (from first-principles search):")
    print(f"   - Based on {len(valid_tiles)} tiles at z{Z}")
    print(f"   - Bounding Box: {discovered_bbox}")


if __name__ == "__main__":
    main() 