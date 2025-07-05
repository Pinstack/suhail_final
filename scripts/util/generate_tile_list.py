import logging

import httpx
import mercantile
import geopandas as gpd
from shapely.ops import unary_union
from tqdm import tqdm

from meshic_pipeline.decoder.mvt_decoder import MVTDecoder

# --- Configuration ---
LOG_LEVEL = logging.INFO
BASE_URL = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
TARGET_ZOOM = 15
DISCOVERY_ZOOM = 5
TARGET_LAYER = "parcels" # Correct layer discovered via inspection
OUTPUT_FILE = "tile_list.txt"

# The single z5 tile that covers the Riyadh region
DISCOVERY_TILE = (DISCOVERY_ZOOM, 20, 13)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

# --- Setup ---
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

def main():
    """
    Generates a precise list of high-zoom tiles needed to cover the data
    footprint discovered at a lower zoom level.
    """
    logging.info(f"--- Starting Tile List Generation ---")
    
    # 1. Download the low-zoom discovery tile
    z, x, y = DISCOVERY_TILE
    url = BASE_URL.format(z=z, x=x, y=y)
    logging.info(f"Downloading discovery tile: {url}")
    
    try:
        with httpx.Client(headers=HEADERS) as client:
            response = client.get(url, timeout=30)
            response.raise_for_status()
            tile_data = response.content
    except httpx.RequestError as e:
        logging.error(f"Failed to download discovery tile: {e}")
        return

    logging.info(f"Successfully downloaded {len(tile_data)} bytes.")

    # 2. Decode the tile and extract the target layer
    decoder = MVTDecoder()
    gdfs = decoder.decode_to_gdf(tile_data, z, x, y, layers=[TARGET_LAYER])
    
    parcels_gdf = gdfs.get(TARGET_LAYER)
    if parcels_gdf is None or parcels_gdf.empty:
        logging.error(f"Target layer '{TARGET_LAYER}' not found or is empty in the discovery tile.")
        return
        
    logging.info(f"Found {len(parcels_gdf)} features in layer '{TARGET_LAYER}'.")
    
    # 3. Clean invalid geometries using a zero-width buffer
    # This is a standard trick to fix topology errors.
    cleaned_geometries = parcels_gdf.geometry.buffer(0)
    logging.info("Cleaned up geometries to prevent topology errors.")

    # 4. Create a single "master polygon" from all features
    master_polygon = unary_union(cleaned_geometries)
    logging.info(f"Created master polygon from all features.")

    # 5. Get the precise bounding box of the master polygon
    bbox = master_polygon.bounds
    logging.info(f"Master polygon bounding box: {bbox}")

    # 6. Generate all high-zoom tiles that intersect this bounding box
    tiles_to_process = list(mercantile.tiles(*bbox, zooms=[TARGET_ZOOM]))
    logging.info(f"Generated {len(tiles_to_process)} tiles at z{TARGET_ZOOM} to cover the master polygon.")
    
    # 7. Save the list of tiles to a file
    with open(OUTPUT_FILE, 'w') as f:
        for tile in tiles_to_process:
            f.write(f"{tile.z},{tile.x},{tile.y}\\n")
            
    logging.info(f"Successfully saved tile list to '{OUTPUT_FILE}'.")
    print(f"\\n✅ Done. A list of {len(tiles_to_process)} tiles has been saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 
