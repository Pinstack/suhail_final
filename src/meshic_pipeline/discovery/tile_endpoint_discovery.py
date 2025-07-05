from __future__ import annotations

from typing import List, Tuple

import mercantile


def get_tile_coordinates_for_bounds(
    bbox: Tuple[float, float, float, float], zoom: int
) -> List[Tuple[int, int, int]]:
    """Return list of (z, x, y) tiles covering bbox at given zoom."""
    west, south, east, north = bbox
    return [(t.z, t.x, t.y) for t in mercantile.tiles(west, south, east, north, [zoom])]

def get_tile_coordinates_for_grid(
    center_x: int, center_y: int, grid_w: int, grid_h: int, zoom: int
) -> List[Tuple[int, int, int]]:
    """Return list of (z, x, y) tiles for a grid centered at a tile."""
    start_x = center_x - grid_w // 2
    start_y = center_y - grid_h // 2
    
    tiles = []
    for i in range(grid_w):
        for j in range(grid_h):
            tiles.append((zoom, start_x + i, start_y + j))
            
    return tiles 
