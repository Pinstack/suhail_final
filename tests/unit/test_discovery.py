import mercantile
from meshic_pipeline.discovery.tile_endpoint_discovery import (
    get_tile_coordinates_for_bounds,
    get_tile_coordinates_for_grid,
)


def test_get_tile_coordinates_for_bounds_round_trip():
    bbox = (46.0, 24.0, 46.1, 24.1)
    zoom = 15
    tiles = get_tile_coordinates_for_bounds(bbox, zoom)
    expected = [(t.z, t.x, t.y) for t in mercantile.tiles(*bbox, zooms=[zoom])]
    assert tiles == expected


def test_get_tile_coordinates_for_grid_size():
    tiles = get_tile_coordinates_for_grid(10, 10, 3, 3, 15)
    assert len(tiles) == 9
    assert tiles[0] == (15, 9, 9)
