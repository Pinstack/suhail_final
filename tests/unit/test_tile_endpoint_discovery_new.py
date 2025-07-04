import pytest
from src.meshic_pipeline.discovery.tile_endpoint_discovery import (
    get_tile_coordinates_for_bounds,
    get_tile_coordinates_for_grid,
)


def test_get_tile_coordinates_for_bounds_single_tile():
    bbox = (0.0, 0.0, 1.0, 1.0)
    tiles = get_tile_coordinates_for_bounds(bbox, zoom=1)
    assert tiles == [(1, 1, 0)]


def test_get_tile_coordinates_for_bounds_invalid():
    bbox = (1.0, 1.0, 0.0, 0.0)
    tiles = get_tile_coordinates_for_bounds(bbox, zoom=1)
    assert tiles == []


def test_get_tile_coordinates_for_grid():
    tiles = get_tile_coordinates_for_grid(
        center_x=5, center_y=6, grid_w=3, grid_h=2, zoom=4
    )
    expected = [
        (4, 4, 5),
        (4, 4, 6),
        (4, 5, 5),
        (4, 5, 6),
        (4, 6, 5),
        (4, 6, 6),
    ]
    assert tiles == expected
