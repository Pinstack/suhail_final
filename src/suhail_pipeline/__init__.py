from .pipeline_orchestrator import (
    run_pipeline,
    get_tile_coordinates_for_grid,
    get_tile_coordinates_for_bounds,
)

__all__ = [
    "run_pipeline",
    "get_tile_coordinates_for_grid",
    "get_tile_coordinates_for_bounds",
]

# Provide discovery helpers as convenient globals for legacy tests/tools
try:
    import builtins  # type: ignore

    builtins.get_tile_coordinates_for_grid = get_tile_coordinates_for_grid
    builtins.get_tile_coordinates_for_bounds = get_tile_coordinates_for_bounds
except Exception:
    # Builtins import may fail in restricted environments; ignore gracefully
    pass
