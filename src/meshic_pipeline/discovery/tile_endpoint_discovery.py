from __future__ import annotations

from typing import List, Tuple

import mercantile


def get_tile_coordinates_for_bounds(
    bbox: Tuple[float, float, float, float], zoom: int
) -> List[Tuple[int, int, int]]:
    """Return list of (z, x, y) tiles covering bbox at given zoom."""
    west, south, east, north = bbox
    return [(t.z, t.x, t.y) for t in mercantile.tiles(west, south, east, north, [zoom])] 