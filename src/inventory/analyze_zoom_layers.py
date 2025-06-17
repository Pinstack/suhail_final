"""Analyze layer coverage across zoom levels.

Usage:
    python -m src.inventory.analyze_zoom_layers \
        --min-zoom 11 --max-zoom 15 \
        --layers parcels,parcels-base,parcels-centroids,neighborhoods,neighborhoods-centroids,subdivisions,dimensions,sb_area,metro_lines,bus_lines,metro_stations,riyadh_bus_stations,qi_population_metrics,qi_stripes \
        --bbox 24.4 46.5 24.9 47.2  # Riyadh approx (miny minx maxy maxx)

Outputs a markdown table mapping layer → feature_count per zoom and prints the minimal zoom that attains full count (within tolerance).

Note: Streets layer intentionally excluded.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import aiohttp
import mercantile
import pandas as pd
import mapbox_vector_tile

from src.decoder.mvt_decoder import MVTDecoder  # type: ignore

# ---------------------------------------------------------------------------
TILE_URL_TEMPLATE = "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
async def fetch_tile(session: aiohttp.ClientSession, z: int, x: int, y: int) -> bytes | None:
    url = TILE_URL_TEMPLATE.format(z=z, x=x, y=y)
    cache_path = CACHE_DIR / f"{z}_{x}_{y}.pbf"
    if cache_path.exists():
        return cache_path.read_bytes()
    async with session.get(url) as resp:
        if resp.status == 404:
            logging.debug("Tile %s not found", url)
            return None
        resp.raise_for_status()
        data = await resp.read()
        cache_path.write_bytes(data)
        return data


async def collect_tiles_data(
    session: aiohttp.ClientSession, tiles: Sequence[mercantile.Tile], layers: Sequence[str]
) -> Dict[str, List[int]]:
    decoder = MVTDecoder()
    counts: Dict[str, List[int]] = {lyr: [] for lyr in layers}
    for tile in tiles:
        raw = await fetch_tile(session, tile.z, tile.x, tile.y)
        if raw is None:
            continue
        decoded = decoder.decode_bytes(raw, layers)
        for layer, feats in decoded.items():
            counts[layer].append(len(feats))
    return counts


async def analyze_single_chain(
    start_tile: mercantile.Tile,
    min_zoom: int,
    layers: List[str] | None,
    tolerance: float = 0.02,
    exclude_layers: Sequence[str] | None = None,
):
    """Analyze parent-tile chain from start_tile.z down to min_zoom."""
    exclude_layers = set(exclude_layers or [])
    async with aiohttp.ClientSession() as session:
        # ensure layers known via start tile when not provided
        if layers is None:
            raw = await fetch_tile(session, start_tile.z, start_tile.x, start_tile.y)
            if raw is None:
                raise RuntimeError("Start tile not found")
            all_layers = mapbox_vector_tile.decode(raw).keys()
            layers = [lyr for lyr in all_layers if lyr not in exclude_layers]

        results = []
        tile = start_tile
        while tile.z >= min_zoom:
            logging.info("Zoom %d tile %d %d", tile.z, tile.x, tile.y)
            counts = await collect_tiles_data(session, [tile], layers)
            for layer, cts in counts.items():
                results.append({"zoom": tile.z, "layer": layer, "features": sum(cts)})
            # move to parent
            if tile.z == min_zoom:
                break
            tile = mercantile.parent(tile)

    df = pd.DataFrame(results)
    tbl = df.pivot(index="layer", columns="zoom", values="features").fillna(0).astype(int)
    # Determine minimal zoom where count within tolerance of max.
    mapping = {}
    for layer, row in tbl.iterrows():
        mx = row.max()
        best = row[row >= mx * (1 - tolerance)].idxmin()
        mapping[layer] = best
    print("\nRecommended minimal zoom per layer (≤2% feature loss):")
    for layer, zoom in mapping.items():
        print(f"{layer}: {zoom}")
    print("\nFull table:")
    print(tbl.to_markdown())

    # Optionally save CSV
    csv_path = Path("layer_zoom_counts.csv")
    tbl.to_csv(csv_path)
    logging.info("Counts written to %s", csv_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze layer coverage across zoom levels.")
    parser.add_argument("--tile", type=str, default="15,20636,14069", help="Start tile as 'z,x,y'")
    parser.add_argument("--min-zoom", type=int, default=1)
    parser.add_argument("--max-zoom", type=int, default=15)
    parser.add_argument("--layers", type=str, help="Comma-separated layer names (optional)")
    parser.add_argument("--exclude", type=str, default="streets", help="Comma-separated layers to exclude")
    parser.add_argument("--tolerance", type=float, default=0.02)
    args = parser.parse_args()

    z, x, y = (int(v) for v in args.tile.split(","))
    start_tile = mercantile.Tile(x, y, z)
    if args.min_zoom > z:
        raise SystemExit("--min-zoom cannot exceed start tile zoom")

    layers = [l.strip() for l in args.layers.split(",")] if args.layers else None
    exclude_layers = [l.strip() for l in args.exclude.split(",") if l]

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    asyncio.run(analyze_single_chain(start_tile, args.min_zoom, layers, args.tolerance, exclude_layers)) 