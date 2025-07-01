from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define project root independently
# Resolves to the parent directory of 'src', which is the project's root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    """
    Pipeline configuration loaded from environment variables and/or a .env file.
    Provides robust, typed settings for the entire application.
    """

    # --- Model Meta Configuration ---
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core Settings ---
    database_url: PostgresDsn = Field(
        ...,
        description="Full database connection string (e.g., postgresql://user:pass@host/db)",
    )
    tile_base_url: str = Field(
        "https://tiles.suhail.ai/maps/riyadh",
        description="Base URL for the MVT tile server, without /z/x/y.",
    )
    default_crs: str = Field("EPSG:4326", description="Default CRS for all GeoDataFrames")

    # --- Caching and Directories ---
    project_root: Path = PROJECT_ROOT
    cache_dir: Path = PROJECT_ROOT / "tiles_cache"
    temp_dir: Path = PROJECT_ROOT / "temp_tiles"
    stitched_dir: Path = PROJECT_ROOT / "stitched"

    # --- Concurrency and Performance ---
    max_concurrent_downloads: int = Field(
        20, description="Maximum number of concurrent tile download requests."
    )
    db_chunk_size: int = Field(
        5000, description="Number of rows to write to the database in a single batch."
    )
    request_delay_seconds: float = Field(
        0.05, description="Small delay between download requests to avoid overwhelming the server."
    )

    # --- Logging ---
    log_level: str = Field("INFO", description="Logging level (e.g., DEBUG, INFO, WARNING)")
    log_file: Optional[str] = Field(
        "pipeline.log", description="File to write logs to. If None, logs to console."
    )

    # --- Layer-specific Behavior ---
    id_column_per_layer: Dict[str, str] = Field(
        default_factory=lambda: {
            "parcels": "parcel_id",
            "parcels-base": "parcel_id",
            "parcels-centroids": "parcel_id",
            "subdivisions": "subdivision_id",
            "neighborhoods": "neighborhood_id",
            "neighborhoods-centroids": "neighborhood_id",
            "qi_stripes": "strip_id",
            "sb_area": "name",  # Use the 'name' field as the unique identifier
        },
        description="Column to use as the unique ID for dissolving geometries, per layer.",
    )

    aggregation_rules_per_layer: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {
            "parcels": {"area_sqm": "first", "district_id": "first"},
            "subdivisions": {"name": "first", "area_sqm": "first"},
            "neighborhoods": {"name": "first", "area_sqm": "first"},
        },
        description="Attribute aggregation rules for GeoPandas dissolve, per layer.",
    )

    table_name_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "parcels-base": "parcels_base",
            "parcels-centroids": "parcels_centroids",
            "neighborhoods-centroids": "neighborhoods_centroids",
            "metro_lines": "metro_lines",
            "bus_lines": "bus_lines",
            "metro_stations": "metro_stations",
            "riyadh_bus_stations": "riyadh_bus_stations",
            "qi_population_metrics": "qi_population_metrics",
            "qi_stripes": "qi_stripes",
        },
        description="Mapping from layer name to the desired PostGIS table name.",
    )
    
    layers_to_process: List[str] = Field(
        default_factory=lambda: [
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
        ],
        description="A list of all layer names to be processed by the pipeline.",
    )

    # --- Methods ---
    def get_tile_cache_path(self, z: int, x: int, y: int) -> Path:
        """Constructs the cache path for a specific tile."""
        tile_dir = self.cache_dir / str(z) / str(x)
        return tile_dir / f"{y}.pbf"

    @model_validator(mode="after")
    def ensure_dirs(self) -> "Settings":
        """Creates all necessary directories if they don't already exist."""
        for d in (self.cache_dir, self.temp_dir, self.stitched_dir):
            d.mkdir(parents=True, exist_ok=True)
        return self


# --- Global Instance ---
# A single, globally-accessible instance of the settings.
settings = Settings() 