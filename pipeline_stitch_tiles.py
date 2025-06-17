import os
import subprocess
import logging
import yaml
import fiona
import geopandas as gpd
from geometry_stitcher import GeometryStitcher  # assuming class saved as geometry_stitcher.py
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration --------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# -----------------------------------------------------------------
# Load YAML config
with open("pipeline_config.yaml") as f:
    CONFIG = yaml.safe_load(f)

Z = CONFIG["zoom"]
CENTER_X = CONFIG["center_x"]
CENTER_Y = CONFIG["center_y"]
GRID_W = CONFIG["grid_w"]
GRID_H = CONFIG["grid_h"]

# Mapping: layer -> ID column used for stitching
LAYER_ID_MAP = CONFIG["layers"]  # may contain 'auto' or null

TEMP_DIR = "temp_tiles"
OUT_DIR = "stitched"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# Build tile list ------------------------------------------------
TILES = [(Z, CENTER_X + dx, CENTER_Y + dy)
         for dx in range(GRID_W)
         for dy in range(GRID_H)]

# Step 1: Transform tiles per layer (parallel) ------------------


def run_transform(layer: str, z: int, x: int, y: int) -> str:
    """Run transform script for one tile/layer; return output path."""
    tile_file = f"{z}_{x}_{y}.pbf"
    out_path = os.path.join(TEMP_DIR, f"{layer}_{z}_{x}_{y}.geojson")
    if os.path.exists(out_path):
        return out_path
    cmd = [
        "python", "Transform_single_tile.py", layer,
        "--tile", tile_file,
        "--output", out_path,
        "--z", str(z), "--x", str(x), "--y", str(y)
    ]
    logging.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)
    return out_path


# Use ThreadPoolExecutor (I/O bound)
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = []
    for z, x, y in TILES:
        for layer in LAYER_ID_MAP.keys():
            futures.append(executor.submit(run_transform, layer, z, x, y))
    for fut in as_completed(futures):
        try:
            fut.result()
        except subprocess.CalledProcessError as e:
            logging.error("Transform failed: %s", e)

def read_layer(path: str) -> gpd.GeoDataFrame:
    """Read GeoJSON with geometry fix for invalid shapes."""
    return gpd.read_file(path, engine="pyogrio", on_invalid="fix")

# Step 2: Stitch per layer --------------------------------------
stitched = GeometryStitcher()
for layer, id_col in LAYER_ID_MAP.items():
    layer_files = [os.path.join(TEMP_DIR, f"{layer}_{z}_{x}_{y}.geojson") for z, x, y in TILES]
    gdfs = []
    for f in layer_files:
        if not os.path.exists(f) or os.path.getsize(f) == 0:
            continue
        try:
            gdf = read_layer(f)
            # ensure geometry column exists and has at least one non-empty geometry
            if gdf.empty or gdf.geometry.is_empty.all():
                continue
            gdfs.append(gdf)
        except Exception as e:
            logging.warning("Failed reading %s: %s", f, e)
            continue
    if not gdfs:
        continue
    logging.info(f"Stitching layer '{layer}' with {len(gdfs)} tiles...")
    # Auto-detect ID if set to 'auto'
    id_col = id_col or None
    if id_col == 'auto':
        # pick first column ending with '_id'
        for col in gdfs[0].columns:
            if col.lower().endswith('_id'):
                id_col = col
                logging.info(f"Auto-detected ID column '{id_col}' for layer '{layer}'.")
                break
    try:
        stitched_gdf = stitched.stitch_geometries(gdfs, id_column=id_col, target_crs="EPSG:4326")
        out_path = os.path.join(OUT_DIR, f"{layer}_stitched.geojson")
        stitched_gdf.to_file(out_path, driver="GeoJSON")
        logging.info(f"  -> wrote {len(stitched_gdf)} features to {out_path}")
    except Exception as e:
        logging.error(f"Error stitching layer {layer}: {e}") 