from __future__ import annotations

from pathlib import Path
from typing import Sequence, Tuple

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    """Central configuration for the scraper/stitcher pipeline."""

    # ---------------------------------------------------------------------
    # Core parameters ------------------------------------------------------
    # ---------------------------------------------------------------------
    database_url: str = Field(
        ..., env="DATABASE_URL", description="SQLAlchemy/PostGIS connection URL"
    )
    aoi_bbox: Tuple[float, float, float, float] = Field(
        ..., description="AOI bbox in lon_min, lat_min, lon_max, lat_max (EPSG:4326)"
    )
    zoom: int = Field(15, description="Zoom level to download and process")
    layers: Sequence[str] = Field(
        (
            "parcels",
            "parcels-base",
            "parcels-centroids",
            "neighborhoods",
            "neighborhoods-centroids",
            "subdivisions",
            "dimensions",
            "sb_area",
            "metro_lines",
            "bus_lines",
            "metro_stations",
            "riyadh_bus_stations",
            "qi_population_metrics",
            "qi_stripes",
        ),
        description="Layer names present in the tiles to extract (streets excluded)",
    )

    cache_dir: Path = Field(Path("tiles_cache"), description="Directory for cached tiles")
    temp_dir: Path = Field(Path("temp_tiles"), description="Directory for temporary GeoJSONs")
    stitched_dir: Path = Field(Path("stitched"), description="Directory for stitched outputs")
    max_concurrent: int = Field(32, description="Concurrent tile downloads")

    # ------------------------------------------------------------------
    def get_tile_cache_path(self, z: int, x: int, y: int) -> Path:
        return self.cache_dir / str(z) / str(x) / f"{y}.pbf"

    def ensure_dirs(self) -> None:
        for d in (self.cache_dir, self.temp_dir, self.stitched_dir):
            d.mkdir(parents=True, exist_ok=True) 