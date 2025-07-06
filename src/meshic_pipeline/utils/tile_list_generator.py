from __future__ import annotations

from typing import Dict, List, Tuple


def tiles_from_bbox_z(
    bbox: Dict[str, int],
    zoom: int = 15,
) -> List[Tuple[int, int, int]]:
    """Generate exhaustive tile coordinates for a bounding box at zoom level."""
    min_x = bbox["min_x"]
    max_x = bbox["max_x"]
    min_y = bbox["min_y"]
    max_y = bbox["max_y"]
    tiles = []
    for x in range(min_x, max_x + 1):
        for y in range(min_y, max_y + 1):
            tiles.append((zoom, x, y))
    return tiles
