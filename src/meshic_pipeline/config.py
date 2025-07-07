from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
import yaml

from pydantic import Field, PostgresDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Define project root independently
# Resolves to the parent directory of 'src', which is the project's root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Load pipeline configuration
PIPELINE_CONFIG_PATH = PROJECT_ROOT / 'pipeline_config.yaml'
PIPELINE_CFG = yaml.safe_load(PIPELINE_CONFIG_PATH.read_text())

# Load province metadata for province-wide processing
PROVINCES_PATH = PROJECT_ROOT / 'provinces.yaml'
if PROVINCES_PATH.exists():
    PROVINCES_DATA = yaml.safe_load(PROVINCES_PATH.read_text())
else:
    PROVINCES_DATA = {}

# Centralized mapping for all Arabic/text columns to canonical _ar names
ARABIC_COLUMN_MAP = {
    "neighborhaname": "neighborhood_ar",
    "neighborh_aname": "neighborhood_ar",  # Source distinguishes Arabic name with this field
    "provinceaname": "province_ar",
    "province_aname": "province_ar",
    "regionaname": "region_ar",
    "region_aname": "region_ar",
    "cityaname": "city_ar",
    "city_aname": "city_ar",
    "building_rule_aname": "building_rule_ar",
    "description_aname": "description_ar",
    "name_aname": "name_ar",
    # Add any other discovered or future Arabic columns here
}

class Environment(str, Enum):
    """Environment types for configuration management."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

class MemoryConfig(BaseSettings):
    """Configuration for in-memory caching and performance monitoring."""
    max_cached_objects: int = Field(
        1000,
        description="Maximum number of objects to hold in memory for performance logging.",
    )
    max_memory_usage_mb: int = Field(
        1024,
        alias="MAX_MEMORY_MB",
        description="Soft memory limit in MB before garbage collection is triggered.",
    )
    enable_memory_monitoring: bool = Field(
        True,
        alias="ENABLE_MEMORY_MONITORING",
        description="Enable periodic memory checks and automatic garbage collection.",
    )

class RetryConfig(BaseSettings):
    """Configuration for network request retries."""
    max_attempts: int = Field(3, description="Maximum number of retry attempts.")
    base_delay: int = Field(1, description="Base delay in seconds for exponential backoff.")
    max_delay: int = Field(60, description="Maximum delay in seconds between retries.")

class DBPoolConfig(BaseSettings):
    """Configuration for the database connection pool."""
    min_size: int = Field(5, description="Minimum number of connections in the pool.")
    max_size: int = Field(20, description="Maximum number of connections in the pool.")
    timeout: int = Field(30, description="Connection acquisition timeout in seconds.")
    command_timeout: int = Field(60, description="Timeout for individual DB commands.")
    pool_pre_ping: bool = Field(True, description="Enable connection health checks.")
    pool_recycle: int = Field(3600, description="Recycle connections after this many seconds.")
    echo_pool: bool = Field(False, description="Log connection pool events.")

class ApiConfig(BaseSettings):
    """Configuration for external Suhail API endpoints."""
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    base_url: str = Field(
        "https://api2.suhail.ai",
        alias="SUHAIL_API_BASE_URL",
        description="Base URL for the Suhail API"
    )
    timeout: int = Field(60, description="Total timeout in seconds for API calls")
    api_key: Optional[str] = Field(
        None,
        alias="SUHAIL_API_KEY",
        description="API key for authentication"
    )
    transactions_url: Optional[str] = Field(None, description="Full Transactions API URL")
    building_rules_url: Optional[str] = Field(None, description="Full Building Rules API URL")
    price_metrics_url: Optional[str] = Field(None, description="Full Price Metrics API URL")

    @model_validator(mode="after")
    def build_urls(self) -> "ApiConfig":
        """Populate full endpoint URLs based on the base_url if not explicitly provided."""
        if not self.transactions_url:
            self.transactions_url = f"{self.base_url}/transactions"
        if not self.building_rules_url:
            self.building_rules_url = f"{self.base_url}/parcel/buildingRules"
        if not self.price_metrics_url:
            self.price_metrics_url = f"{self.base_url}/api/parcel/metrics/priceOfMeter"
        return self

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

    # --- Nested Configurations ---
    memory_config: MemoryConfig = Field(default_factory=MemoryConfig)
    retry_config: RetryConfig = Field(default_factory=RetryConfig)
    db_pool: DBPoolConfig = Field(default_factory=DBPoolConfig)
    api_config: ApiConfig = Field(default_factory=ApiConfig)

    # --- Environment Configuration ---
    environment: Environment = Field(
        Environment.DEVELOPMENT,
        description="Current environment (development, testing, staging, production)"
    )
    debug: bool = Field(False, description="Enable debug mode")

    # --- Core Settings ---
    database_url: PostgresDsn = Field(
        ...,
        description="Full database connection string (e.g., postgresql://user:pass@host/db)",
    )
    tile_base_url: str = Field(
        "https://tiles.suhail.ai/maps/riyadh",
        alias="TILE_BASE_URL",
        description="Base URL for the MVT tile server, without /z/x/y."
    )
    default_crs: str = Field("EPSG:4326", description="Default CRS for all GeoDataFrames")
    # --- Pipeline Grid Configuration (loaded from pipeline_config.yaml) ---
    zoom: int = Field(PIPELINE_CFG.get('zoom', 15), description="Tile zoom level from pipeline_config.yaml")
    center_x: int = Field(PIPELINE_CFG.get('center_x'), description="Tile grid center x coordinate")
    center_y: int = Field(PIPELINE_CFG.get('center_y'), description="Tile grid center y coordinate")
    grid_w: int = Field(PIPELINE_CFG.get('grid_w'), description="Tile grid width from pipeline_config.yaml")
    grid_h: int = Field(PIPELINE_CFG.get('grid_h'), description="Tile grid height from pipeline_config.yaml")

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
            "parcels": "parcel_objectid",
            "parcels-centroids": "parcel_no",
            "subdivisions": "subdivision_id",
            "neighborhoods": "neighborhood_id",
            "neighborhoods-centroids": "neighborhood_id",
            "dimensions": "parcel_objectid",
            "metro_stations": "station_code",
            "riyadh_bus_stations": "station_code",
            "qi_population_metrics": "grid_id",
            "qi_stripes": "strip_id",
        },
        description="Column to use as the unique ID for dissolving geometries, per layer. Only tables with unique constraints should be listed here.",
    )

    aggregation_rules_per_layer: Dict[str, Dict[str, str]] = Field(
        default_factory=lambda: {
            "parcels": {
                "shape_area": "first",
                "transaction_price": "first",
                "price_of_meter": "first", 
                "landuseagroup": "first",
                "zoning_id": "first",
                "subdivision_id": "first",
                "neighborhood_ar": "first",
                "parcel_no": "first",
                "subdivision_no": "first",
                "zoning_color": "first"
            },
            "parcels-centroids": {
                "transaction_date": "first",
                "transaction_price": "first", 
                "price_of_meter": "first"
            },
            "neighborhoods": {
                "shape_area": "first",
                "region_id": "first",
                "province_id": "first", 
                "zoning_id": "first",
                "zoning_color": "first",
                "neighborhood_ar": "first",
                "transaction_price": "first",
                "price_of_meter": "first"
            },
            "subdivisions": {
                "shape_area": "first",
                "subdivision_no": "first",
                "zoning_id": "first",
                "zoning_color": "first",
                "transaction_price": "first",
                "price_of_meter": "first"
            },
        },
        description="Attribute aggregation rules for GeoPandas dissolve, per layer.",
    )

    table_name_mapping: Dict[str, str] = Field(
        default_factory=lambda: {
            "parcels": "parcels",
            "parcels-centroids": "parcels_centroids",
            "neighborhoods": "neighborhoods",
            "neighborhoods-centroids": "neighborhoods_centroids",
            "subdivisions": "subdivisions",
            "metro_lines": "metro_lines",
            "bus_lines": "bus_lines",
            "metro_stations": "metro_stations",
            "riyadh_bus_stations": "riyadh_bus_stations",
            "qi_population_metrics": "qi_population_metrics",
            "qi_stripes": "qi_stripes",
        },
        description="Mapping from layer name to the desired PostGIS table name.",
    )

    # --- Province Metadata ---
    provinces: Dict[str, Any] = Field(default_factory=lambda: PROVINCES_DATA)
    
    layers_to_process: List[str] = Field(
        default_factory=lambda: [
            "neighborhoods",
            "subdivisions",
            "parcels",
            "parcels-centroids",
            "neighborhoods-centroids",
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

    def get_province_meta(self, province: str) -> Dict[str, Any]:
        """Return metadata for a given province."""
        if province not in self.provinces:
            raise KeyError(f"Unknown province: {province}")
        return self.provinces[province]

    def list_provinces(self) -> List[str]:
        """Return available province keys."""
        return list(self.provinces.keys())

    def is_production(self) -> bool:
        """Check if the current environment is production."""
        return self.environment == Environment.PRODUCTION

    @model_validator(mode="after")
    def ensure_dirs(self) -> "Settings":
        """Creates all necessary directories if they don't already exist."""
        for d in (self.cache_dir, self.temp_dir, self.stitched_dir):
            d.mkdir(parents=True, exist_ok=True)
        return self

    def should_trigger_gc(self, process_mb: float) -> bool:
        """Determine if memory usage warrants garbage collection."""
        limit = self.memory_config.max_memory_usage_mb
        if limit <= 0:
            return False
        return process_mb > limit * 0.9

    def get_optimized_batch_size(
        self, base_batch_size: int, item_size_estimate_kb: float = 10.0
    ) -> int:
        """Return a batch size based on configuration limits."""
        return base_batch_size


# --- Global Instance ---
# A single, globally-accessible instance of the settings.
settings = Settings() 
