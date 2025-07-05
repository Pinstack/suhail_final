import asyncio
import json
import logging
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import shutil

import httpx
import mercantile
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import box
import typer

from meshic_pipeline.decoder.mvt_decoder import MVTDecoder

# --- Enhanced Configuration ---
LOG_LEVEL = logging.INFO
TARGET_ZOOM = 15
DISCOVERY_ZOOM = 10  # Use API-recommended zoom level
SAMPLE_GRID_SIZE = 3  # 3x3 grid of discovery tiles
TARGET_LAYER = "parcels"
ENRICHMENT_LAYERS = ["parcels", "zoning", "boundaries"]  # Additional layers from modes endpoint
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

# Resource Management Thresholds
MAX_STORAGE_GB = 100  # Maximum storage per province before warning
MAX_PROCESSING_HOURS = 24  # Maximum estimated processing time
MIN_PARCELS_THRESHOLD = 100  # Minimum parcels to consider province viable

@dataclass
class ProvinceConfig:
    """Configuration for a Saudi province"""
    name: str
    tile_server_name: str  # Name used in tile URL
    priority: int  # 1 = highest priority
    approximate_bbox: Tuple[float, float, float, float]  # (west, south, east, north)
    discovery_tile: Optional[Tuple[int, int, int]] = None  # (z, x, y) - auto-calculated if None
    estimated_population: Optional[int] = None
    economic_importance: int = 1  # 1-5 scale
    suhail_metrics_url: Optional[str] = None  # Suhail.ai metrics URL

@dataclass
class ResourceEstimate:
    """Resource requirements estimate for a province"""
    province_name: str
    parcels_in_discovery_tile: int
    estimated_total_parcels: int
    high_zoom_tiles_count: int
    precise_bbox: Tuple[float, float, float, float]
    storage_gb: float
    processing_hours: float
    api_calls_estimated: int
    recommendation: str
    viability: str  # "high", "medium", "low", "skip"

@dataclass
class DiscoveryResult:
    """Complete discovery result for a province"""
    province_config: ProvinceConfig
    resource_estimate: Optional[ResourceEstimate]
    discovery_tile_used: Tuple[int, int, int]
    has_data: bool
    error_message: Optional[str] = None

# --- Province Configurations (Updated with Suhail.ai exact names) ---
SAUDI_PROVINCES = {
    "riyadh": ProvinceConfig(
        name="Riyadh",
        tile_server_name="riyadh", 
        priority=1,
        approximate_bbox=(46.265364184769595, 23.986904579297715, 47.342260256150155, 25.781380632818795),  # API restrictBoundaryBox
        estimated_population=8_000_000,
        economic_importance=5,
        suhail_metrics_url="https://www.suhail.ai/Riyadh/metrics"
    ),
    "makkah": ProvinceConfig(
        name="Makkah",
        tile_server_name="makkah_region",  # Corrected server name
        priority=2,
        approximate_bbox=(38.925834, 20.827453, 39.606465, 22.357147),  # API restrictBoundaryBox
        estimated_population=8_500_000,
        economic_importance=5,
        suhail_metrics_url="https://www.suhail.ai/Makkah/metrics"
    ),
    "eastern": ProvinceConfig(
        name="Eastern",
        tile_server_name="eastern_region",
        priority=3,
        approximate_bbox=(49.811760072324375, 25.91230398310188, 50.27967299061834, 26.682884502427413),  # API restrictBoundaryBox
        estimated_population=5_000_000,
        economic_importance=4,
        suhail_metrics_url="https://www.suhail.ai/Eastern/metrics"
    ),
    "madinah": ProvinceConfig(
        name="Madinah",
        tile_server_name="al_madenieh",  # Corrected server name
        priority=2,
        approximate_bbox=(39.4133787747582, 24.091386951345967, 39.90345597984938, 24.91057558068701),  # API restrictBoundaryBox
        estimated_population=2_200_000,
        economic_importance=4,
        suhail_metrics_url="https://www.suhail.ai/Madinah/metrics"
    ),
    "al_qassim": ProvinceConfig(
        name="Al_Qassim",
        tile_server_name="al_qassim",  # Corrected from API
        priority=4,
        approximate_bbox=(43.0, 25.5, 45.0, 27.5),  # API restrictBoundaryBox appears corrupted, using centroid-based estimate
        discovery_tile=(11, 1273, 868),  # Use known working tile from network traffic
        estimated_population=1_400_000,
        economic_importance=3,
        suhail_metrics_url="https://www.suhail.ai/Al_Qassim/metrics"
    ),
    "asir": ProvinceConfig(
        name="Asir",
        tile_server_name="asir_region",  # Corrected from API
        priority=3,
        approximate_bbox=(41.214223, 17.366667, 44.440789, 20.80266),  # API restrictBoundaryBox
        discovery_tile=(5, 19, 14),  # Use known working zoom 5 tile
        estimated_population=2_200_000,
        economic_importance=3,
        suhail_metrics_url="https://www.suhail.ai/Asir/metrics"
    ),
    # Additional provinces for completeness
    "tabuk": ProvinceConfig(
        name="Tabuk",
        tile_server_name="tabuk", 
        priority=5,
        approximate_bbox=(34.5, 27.0, 39.0, 30.0),
        estimated_population=900_000,
        economic_importance=2
    ),
    "hail": ProvinceConfig(
        name="Hail",
        tile_server_name="hail",
        priority=4,
        approximate_bbox=(39.0, 26.0, 42.5, 28.5),
        estimated_population=700_000,
        economic_importance=2
    ),
    "jazan": ProvinceConfig(
        name="Jazan",
        tile_server_name="jazan",
        priority=4,
        approximate_bbox=(42.0, 16.0, 43.5, 18.0),
        estimated_population=1_500_000,
        economic_importance=3
    ),
    "najran": ProvinceConfig(
        name="Najran",
        tile_server_name="najran",
        priority=5,
        approximate_bbox=(43.5, 16.5, 46.0, 18.5),
        estimated_population=600_000,
        economic_importance=2
    ),
    "bahah": ProvinceConfig(
        name="Al Bahah",
        tile_server_name="bahah",
        priority=5,
        approximate_bbox=(41.0, 19.5, 42.0, 20.5),
        estimated_population=500_000,
        economic_importance=2
    ),
    "jouf": ProvinceConfig(
        name="Al Jouf",
        tile_server_name="jouf",
        priority=5,
        approximate_bbox=(38.0, 29.0, 42.0, 31.5),
        estimated_population=500_000,
        economic_importance=2
    ),
    "northern_borders": ProvinceConfig(
        name="Northern Borders",
        tile_server_name="northern_borders",
        priority=5,
        approximate_bbox=(39.0, 30.0, 43.0, 32.0),
        estimated_population=400_000,
        economic_importance=1
    )
}

# --- Setup ---
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s"
)

def calculate_discovery_tile_for_bbox(bbox: Tuple[float, float, float, float], zoom: int = 10) -> Tuple[int, int, int]:
    """Calculate the central discovery tile for a given bounding box"""
    west, south, east, north = bbox
    
    # Find center point
    center_lon = (west + east) / 2
    center_lat = (south + north) / 2
    
    # Convert center to tile coordinates
    tile = mercantile.tile(center_lon, center_lat, zoom)
    return (tile.z, tile.x, tile.y)

def estimate_storage_requirements(parcels_count: int, tiles_count: int) -> float:
    """Estimate storage requirements in GB"""
    
    # Based on current Riyadh data: 9,007 parcels ≈ 50MB total
    base_storage_per_parcel_kb = 50 * 1024 / 9007  # ~5.7 KB per parcel
    
    # Storage breakdown
    geometric_data = parcels_count * base_storage_per_parcel_kb / 1024 / 1024  # GB
    enrichment_data = parcels_count * 1.2 / 1024  # ~1.2 KB per enrichment
    spatial_indexes = geometric_data * 0.3  # ~30% of geometric data
    overhead = (geometric_data + enrichment_data + spatial_indexes) * 0.2  # 20% overhead
    
    total_gb = geometric_data + enrichment_data + spatial_indexes + overhead
    return round(total_gb, 2)

def estimate_processing_time(parcels_count: int) -> float:
    """Estimate processing time in hours"""
    
    # Based on current performance: ~99.3% success rate, moderate API speed
    geometric_processing_rate = 10000  # parcels per hour (estimated)
    enrichment_processing_rate = 1000   # parcels per hour (API limited)
    
    geometric_hours = parcels_count / geometric_processing_rate
    enrichment_hours = parcels_count / enrichment_processing_rate
    
    # Total is not additive (they can run sequentially or in batches)
    total_hours = geometric_hours + enrichment_hours * 0.7  # Some overlap
    return round(total_hours, 2)

def get_viability_recommendation(estimate: ResourceEstimate) -> str:
    """Determine processing recommendation based on estimates"""
    
    if estimate.estimated_total_parcels < MIN_PARCELS_THRESHOLD:
        return "skip"
    elif estimate.storage_gb > MAX_STORAGE_GB:
        return "low"
    elif estimate.processing_hours > MAX_PROCESSING_HOURS:
        return "low" 
    elif estimate.estimated_total_parcels > 50000:
        return "medium"
    else:
        return "high"

def get_recommendation_text(estimate: ResourceEstimate) -> str:
    """Generate human-readable recommendation"""
    
    if estimate.viability == "skip":
        return f"❌ SKIP: Only {estimate.estimated_total_parcels} parcels found - below threshold"
    elif estimate.viability == "low":
        if estimate.storage_gb > MAX_STORAGE_GB:
            return f"⚠️  CAUTION: High storage requirement ({estimate.storage_gb} GB) - consider partitioning"
        else:
            return f"⚠️  CAUTION: Long processing time ({estimate.processing_hours} hours) - schedule carefully"
    elif estimate.viability == "medium":
        return f"🔶 MEDIUM: Large dataset ({estimate.estimated_total_parcels:,} parcels) - batch processing recommended"
    else:
        return f"✅ HIGH: Optimal size ({estimate.estimated_total_parcels:,} parcels) - ready for processing"

async def download_discovery_tile(province_config: ProvinceConfig, discovery_tile: Tuple[int, int, int]) -> Optional[bytes]:
    """Download a single discovery tile for the province"""
    
    z, x, y = discovery_tile
    base_url = f"https://tiles.suhail.ai/maps/{province_config.tile_server_name}"
    url = f"{base_url}/{z}/{x}/{y}.vector.pbf"
    
    logging.info(f"Downloading discovery tile for {province_config.name}: {url}")
    
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.get(url, timeout=30)
            response.raise_for_status()
            
            if len(response.content) < 200:  # Suspiciously small tile
                logging.warning(f"Discovery tile for {province_config.name} is very small ({len(response.content)} bytes)")
                return None
                
            logging.info(f"Successfully downloaded {len(response.content)} bytes for {province_config.name}")
            return response.content
            
    except httpx.RequestError as e:
        logging.error(f"Failed to download discovery tile for {province_config.name}: {e}")
        return None

async def discover_province_data(province_config: ProvinceConfig) -> DiscoveryResult:
    """Discover data extents and estimate resources for a single province"""
    
    logging.info(f"\n--- Discovering data for {province_config.name} ---")
    
    # 1. Determine discovery tile
    if province_config.discovery_tile:
        discovery_tile = province_config.discovery_tile
        logging.info(f"Using configured discovery tile: {discovery_tile}")
    else:
        discovery_tile = calculate_discovery_tile_for_bbox(province_config.approximate_bbox, DISCOVERY_ZOOM)
        logging.info(f"Calculated discovery tile: {discovery_tile}")
    
    # 2. Download discovery tile
    tile_data = await download_discovery_tile(province_config, discovery_tile)
    if not tile_data:
        return DiscoveryResult(
            province_config=province_config,
            resource_estimate=None,
            discovery_tile_used=discovery_tile,
            has_data=False,
            error_message="Failed to download discovery tile"
        )
    
    # 3. Decode MVT and extract parcels
    try:
        decoder = MVTDecoder()
        gdfs = decoder.decode_to_gdf(tile_data, *discovery_tile, layers=[TARGET_LAYER])
        
        parcels_gdf = gdfs.get(TARGET_LAYER)
        if parcels_gdf is None or parcels_gdf.empty:
            logging.warning(f"No parcels found in discovery tile for {province_config.name}")
            return DiscoveryResult(
                province_config=province_config,
                resource_estimate=None,
                discovery_tile_used=discovery_tile,
                has_data=False,
                error_message="No parcel data found in discovery tile"
            )
            
        logging.info(f"Found {len(parcels_gdf)} parcels in discovery tile")
        
    except Exception as e:
        logging.error(f"Failed to decode discovery tile for {province_config.name}: {e}")
        return DiscoveryResult(
            province_config=province_config,
            resource_estimate=None,
            discovery_tile_used=discovery_tile,
            has_data=False,
            error_message=f"MVT decoding failed: {str(e)}"
        )
    
    # 4. Create master polygon and calculate precise bounds
    try:
        cleaned_geometries = parcels_gdf.geometry.buffer(0)
        master_polygon = unary_union(cleaned_geometries)
        precise_bbox = master_polygon.bounds
        
        logging.info(f"Precise bounding box: {precise_bbox}")
        
    except Exception as e:
        logging.error(f"Failed to create master polygon for {province_config.name}: {e}")
        return DiscoveryResult(
            province_config=province_config,
            resource_estimate=None,
            discovery_tile_used=discovery_tile,
            has_data=False,
            error_message=f"Geometry processing failed: {str(e)}"
        )
    
    # 5. Generate high-zoom tiles and estimate totals
    high_zoom_tiles = list(mercantile.tiles(*precise_bbox, zooms=[TARGET_ZOOM]))
    tiles_count = len(high_zoom_tiles)
    
    # Estimate total parcels (scale from discovery tile)
    discovery_tile_area = mercantile.bounds(*discovery_tile)
    
    # Calculate areas more safely with bounds checking
    discovery_width = abs(discovery_tile_area.east - discovery_tile_area.west)
    discovery_height = abs(discovery_tile_area.north - discovery_tile_area.south)
    discovery_area_km2 = discovery_width * discovery_height * 111.32 ** 2
    
    precise_width = abs(precise_bbox[2] - precise_bbox[0])
    precise_height = abs(precise_bbox[3] - precise_bbox[1])
    precise_area_km2 = precise_width * precise_height * 111.32 ** 2
    
    logging.info(f"Discovery area: {discovery_area_km2:.6f} km², Precise area: {precise_area_km2:.6f} km²")
    
    # Safe density calculation with bounds checking
    if discovery_area_km2 > 0 and precise_area_km2 > 0:
        parcel_density = len(parcels_gdf) / discovery_area_km2
        estimated_total_parcels = max(len(parcels_gdf), int(precise_area_km2 * parcel_density))
        logging.info(f"Parcel density: {parcel_density:.2f} parcels/km², Estimated total: {estimated_total_parcels:,}")
    else:
        # Fallback: scale by tile count ratio
        discovery_zoom = discovery_tile[0]
        zoom_scale_factor = 4 ** (TARGET_ZOOM - discovery_zoom)  # Each zoom level = 4x more tiles
        estimated_total_parcels = len(parcels_gdf) * tiles_count // max(1, zoom_scale_factor)
        logging.info(f"Using fallback estimation: {estimated_total_parcels:,} parcels")
    
    # Ensure reasonable bounds
    estimated_total_parcels = max(len(parcels_gdf), min(estimated_total_parcels, 50_000_000))
    
    # 6. Calculate resource estimates
    storage_gb = estimate_storage_requirements(estimated_total_parcels, tiles_count)
    processing_hours = estimate_processing_time(estimated_total_parcels)
    api_calls = estimated_total_parcels * 3  # 3 API endpoints per parcel
    
    # 7. Create resource estimate
    resource_estimate = ResourceEstimate(
        province_name=province_config.name,
        parcels_in_discovery_tile=len(parcels_gdf),
        estimated_total_parcels=estimated_total_parcels,
        high_zoom_tiles_count=tiles_count,
        precise_bbox=precise_bbox,
        storage_gb=storage_gb,
        processing_hours=processing_hours,
        api_calls_estimated=api_calls,
        recommendation="",  # Will be filled below
        viability=""  # Will be filled below
    )
    
    resource_estimate.viability = get_viability_recommendation(resource_estimate)
    resource_estimate.recommendation = get_recommendation_text(resource_estimate)
    
    logging.info(f"Resource estimate completed for {province_config.name}")
    
    return DiscoveryResult(
        province_config=province_config,
        resource_estimate=resource_estimate,
        discovery_tile_used=discovery_tile,
        has_data=True
    )

async def discover_multiple_provinces(province_names: List[str]) -> List[DiscoveryResult]:
    """Discover data for multiple provinces concurrently"""
    
    configs = [SAUDI_PROVINCES[name] for name in province_names if name in SAUDI_PROVINCES]
    if not configs:
        logging.error("No valid province names provided")
        return []
    
    logging.info(f"Starting discovery for {len(configs)} provinces...")
    
    # Run discoveries concurrently (but with some delay to be respectful to server)
    tasks = []
    for i, config in enumerate(configs):
        # Add small delay between requests to be respectful
        if i > 0:
            await asyncio.sleep(1)
        tasks.append(discover_province_data(config))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    valid_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logging.error(f"Discovery failed for {configs[i].name}: {result}")
            valid_results.append(DiscoveryResult(
                province_config=configs[i],
                resource_estimate=None,
                discovery_tile_used=(0, 0, 0),
                has_data=False,
                error_message=str(result)
            ))
        else:
            valid_results.append(result)
    
    return valid_results

def save_discovery_results(results: List[DiscoveryResult], output_dir: str = "province_discovery_results"):
    """Save discovery results to files"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Save summary JSON
    summary_data = []
    for result in results:
        result_dict = {
            "province_name": result.province_config.name,
            "tile_server_name": result.province_config.tile_server_name,
            "priority": result.province_config.priority,
            "has_data": result.has_data,
            "discovery_tile": result.discovery_tile_used,
            "error_message": result.error_message,
            "suhail_metrics_url": result.province_config.suhail_metrics_url
        }
        
        if result.resource_estimate:
            result_dict["resource_estimate"] = asdict(result.resource_estimate)
            
        summary_data.append(result_dict)
    
    summary_file = output_path / "discovery_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    # Save individual tile lists for viable provinces
    for result in results:
        if result.has_data and result.resource_estimate and result.resource_estimate.viability in ["high", "medium"]:
            
            # Generate tile list
            tiles = list(mercantile.tiles(*result.resource_estimate.precise_bbox, zooms=[TARGET_ZOOM]))
            
            tile_file = output_path / f"{result.province_config.tile_server_name}_tiles.txt"
            with open(tile_file, 'w') as f:
                for tile in tiles:
                    f.write(f"{tile.z},{tile.x},{tile.y}\n")
                    
            logging.info(f"Saved {len(tiles)} tiles for {result.province_config.name} to {tile_file}")

def print_discovery_summary(results: List[DiscoveryResult]):
    """Print a comprehensive summary of discovery results"""
    
    print("\n" + "="*80)
    print("🌍 SAUDI ARABIA PROVINCE DISCOVERY SUMMARY")
    print("="*80)
    
    # Sort by priority and viability
    results_with_data = [r for r in results if r.has_data and r.resource_estimate]
    results_with_data.sort(key=lambda x: (x.province_config.priority, x.resource_estimate.viability == "skip"))
    
    total_parcels = sum(r.resource_estimate.estimated_total_parcels for r in results_with_data)
    total_storage = sum(r.resource_estimate.storage_gb for r in results_with_data)
    total_processing = sum(r.resource_estimate.processing_hours for r in results_with_data)
    
    print(f"\n📊 OVERALL STATISTICS:")
    print(f"   • Total Provinces Analyzed: {len(results)}")
    print(f"   • Provinces with Data: {len(results_with_data)}")
    print(f"   • Estimated Total Parcels: {total_parcels:,}")
    print(f"   • Estimated Total Storage: {total_storage:.1f} GB")
    print(f"   • Estimated Total Processing: {total_processing:.1f} hours")
    
    print(f"\n📋 DETAILED RESULTS:")
    
    for result in results:
        print(f"\n🏛️  {result.province_config.name}")
        print(f"   Server: {result.province_config.tile_server_name}")
        print(f"   Priority: {result.province_config.priority}/5")
        if result.province_config.suhail_metrics_url:
            print(f"   Metrics: {result.province_config.suhail_metrics_url}")
        
        if not result.has_data:
            print(f"   Status: ❌ NO DATA - {result.error_message}")
            continue
            
        est = result.resource_estimate
        print(f"   Status: ✅ DATA FOUND")
        print(f"   Discovery Tile: z{result.discovery_tile_used[0]}/{result.discovery_tile_used[1]}/{result.discovery_tile_used[2]}")
        print(f"   Parcels in Discovery: {est.parcels_in_discovery_tile:,}")
        print(f"   Estimated Total Parcels: {est.estimated_total_parcels:,}")
        print(f"   High-Zoom Tiles: {est.high_zoom_tiles_count:,}")
        print(f"   Storage Estimate: {est.storage_gb:.1f} GB")
        print(f"   Processing Estimate: {est.processing_hours:.1f} hours")
        print(f"   API Calls: {est.api_calls_estimated:,}")
        print(f"   {est.recommendation}")
    
    print(f"\n🎯 PROCESSING RECOMMENDATIONS:")
    
    high_priority = [r for r in results_with_data if r.resource_estimate.viability == "high"]
    medium_priority = [r for r in results_with_data if r.resource_estimate.viability == "medium"]
    low_priority = [r for r in results_with_data if r.resource_estimate.viability == "low"]
    
    if high_priority:
        print(f"\n✅ HIGH PRIORITY (Ready for Processing):")
        for r in high_priority:
            print(f"   • {r.province_config.name} - {r.resource_estimate.estimated_total_parcels:,} parcels")
            if r.province_config.suhail_metrics_url:
                print(f"     📊 {r.province_config.suhail_metrics_url}")
    
    if medium_priority:
        print(f"\n🔶 MEDIUM PRIORITY (Batch Processing):")
        for r in medium_priority:
            print(f"   • {r.province_config.name} - {r.resource_estimate.estimated_total_parcels:,} parcels")
            if r.province_config.suhail_metrics_url:
                print(f"     📊 {r.province_config.suhail_metrics_url}")
    
    if low_priority:
        print(f"\n⚠️  LOW PRIORITY (Special Handling Required):")
        for r in low_priority:
            print(f"   • {r.province_config.name} - {r.resource_estimate.storage_gb:.1f} GB / {r.resource_estimate.processing_hours:.1f} hours")
            if r.province_config.suhail_metrics_url:
                print(f"     📊 {r.province_config.suhail_metrics_url}")

# --- CLI Interface ---
app = typer.Typer(help="Intelligent Province Discovery for Saudi Arabia")

@app.command()
def discover(
    provinces: List[str] = typer.Argument(help="Province names to discover (e.g., riyadh makkah eastern)"),
    output_dir: str = typer.Option("province_discovery_results", "--output", "-o", help="Output directory for results"),
    save_results: bool = typer.Option(True, "--save/--no-save", help="Save results to files"),
    show_available: bool = typer.Option(False, "--list", help="Show available provinces and exit")
):
    """Discover data extents and estimate resources for Saudi provinces"""
    
    if show_available:
        print("\n🌍 Available Saudi Provinces:")
        for key, config in SAUDI_PROVINCES.items():
            status = "📊 Has Metrics" if config.suhail_metrics_url else "   No Metrics"
            print(f"   • {key:15} - {config.name} (Priority: {config.priority}) {status}")
            if config.suhail_metrics_url:
                print(f"     {config.suhail_metrics_url}")
        return
    
    if not provinces:
        print("❌ No provinces specified. Use --list to see available provinces.")
        return
    
    # Validate province names
    invalid_provinces = [p for p in provinces if p not in SAUDI_PROVINCES]
    if invalid_provinces:
        print(f"❌ Invalid province names: {invalid_provinces}")
        print("Use --list to see available provinces.")
        return
    
    # Run discovery
    print(f"🚀 Starting intelligent discovery for provinces: {', '.join(provinces)}")
    results = asyncio.run(discover_multiple_provinces(provinces))
    
    # Print summary
    print_discovery_summary(results)
    
    # Save results
    if save_results:
        save_discovery_results(results, output_dir)
        print(f"\n💾 Results saved to: {output_dir}/")
        
        # Show files created
        output_path = Path(output_dir)
        if output_path.exists():
            files = list(output_path.glob("*"))
            for file in files:
                size_mb = file.stat().st_size / 1024 / 1024
                print(f"   • {file.name} ({size_mb:.2f} MB)")

@app.command()
def estimate(
    province: str = typer.Argument(help="Province name for quick estimate"),
    quick: bool = typer.Option(False, "--quick", help="Skip actual tile download, use approximations")
):
    """Quick resource estimate for a single province"""
    
    if province not in SAUDI_PROVINCES:
        print(f"❌ Unknown province: {province}")
        print(f"Available: {', '.join(SAUDI_PROVINCES.keys())}")
        return
    
    config = SAUDI_PROVINCES[province]
    
    if quick:
        # Quick approximation without downloading
        bbox_area = abs(config.approximate_bbox[2] - config.approximate_bbox[0]) * abs(config.approximate_bbox[3] - config.approximate_bbox[1])
        estimated_parcels = int(bbox_area * 10000)  # Rough estimate: 10k parcels per degree²
        
        print(f"\n🔍 QUICK ESTIMATE for {config.name}:")
        print(f"   • Estimated Parcels: ~{estimated_parcels:,}")
        print(f"   • Estimated Storage: ~{estimate_storage_requirements(estimated_parcels, 0):.1f} GB")
        print(f"   • Estimated Processing: ~{estimate_processing_time(estimated_parcels):.1f} hours")
        if config.suhail_metrics_url:
            print(f"   • Metrics URL: {config.suhail_metrics_url}")
        print(f"   \n⚠️  This is a rough approximation. Use 'discover {province}' for accurate estimates.")
    else:
        # Full discovery
        results = asyncio.run(discover_multiple_provinces([province]))
        print_discovery_summary(results)

@app.command()
def suhail_provinces():
    """Run discovery specifically for provinces with Suhail.ai metrics URLs"""
    
    # Get provinces that have Suhail metrics URLs
    suhail_provinces = [key for key, config in SAUDI_PROVINCES.items() if config.suhail_metrics_url]
    
    print(f"🌍 Discovering data for provinces with Suhail.ai metrics:")
    for province in suhail_provinces:
        config = SAUDI_PROVINCES[province]
        print(f"   • {config.name}: {config.suhail_metrics_url}")
    
    print(f"\n🚀 Starting discovery for {len(suhail_provinces)} provinces...")
    results = asyncio.run(discover_multiple_provinces(suhail_provinces))
    
    # Print summary
    print_discovery_summary(results)
    
    # Save results
    save_discovery_results(results, "suhail_provinces_discovery")
    print(f"\n💾 Results saved to: suhail_provinces_discovery/")

if __name__ == "__main__":
    app() 
