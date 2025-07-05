import asyncio
import json
import logging
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import shutil
from collections import defaultdict

import httpx
import mercantile
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import box, Point
import typer
import time

from meshic_pipeline.decoder.mvt_decoder import MVTDecoder

# --- Enhanced Configuration ---
LOG_LEVEL = logging.INFO
TARGET_ZOOM = 15
DISCOVERY_ZOOM_RANGE = [11, 12, 13, 14]  # Multi-zoom discovery based on browser traffic
TARGET_LAYER = "parcels"
ENRICHMENT_LAYERS = ["parcels", "zoning", "boundaries"]
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36"
}

# Resource Management
MAX_STORAGE_GB = 100
MIN_PARCEL_THRESHOLD = 50
MIN_TILE_SIZE_BYTES = 1000  # Lower threshold based on browser traffic

app = typer.Typer(help="Enhanced Saudi Arabia Province Discovery Tool")

@dataclass
class DiscoveryGrid:
    """Grid of discovery tiles for multi-zoom sampling"""
    zoom: int
    tiles: List[Tuple[int, int, int]]  # (z, x, y)
    data_found: bool = False
    total_parcels: int = 0
    total_size_bytes: int = 0

@dataclass
class BrowserTrafficPattern:
    """Real browser traffic patterns for data hotspots"""
    province: str
    zoom_grids: Dict[int, List[Tuple[int, int]]]  # zoom -> [(x,y), ...]
    neighborhood_ids: List[str] = None
    
# --- Known Working Patterns from Browser Traffic ---
BROWSER_TRAFFIC_PATTERNS = {
    "al_qassim": BrowserTrafficPattern(
        province="al_qassim",
        zoom_grids={
            11: [(1273, 868), (1274, 868)],
            12: [(2546, 1736), (2547, 1736), (2548, 1736), (2549, 1736),
                 (2546, 1737), (2547, 1737), (2548, 1737), (2549, 1737)],
            13: [(5094, 3473), (5095, 3473), (5096, 3473),
                 (5094, 3474), (5095, 3474), (5096, 3474)],
            14: [(10190, 6947), (10191, 6947), (10192, 6947)],
            15: [(20381, 13894), (20382, 13894), (20383, 13894),
                 (20381, 13895), (20382, 13895), (20383, 13895)]
        },
        neighborhood_ids=["41000834", "41000778", "41000895", "41000896", "41000892"]
    ),
    "asir": BrowserTrafficPattern(
        province="asir_region",
        zoom_grids={
            11: [(1267, 917), (1266, 917), (1267, 918), (1266, 918)],
            12: [(2534, 1835), (2533, 1835), (2534, 1836), (2533, 1836)],
            13: [(5068, 3672), (5069, 3671), (5069, 3672), (5068, 3671), (5067, 3671), (5067, 3672)],
            14: [(10137, 7343), (10136, 7343), (10135, 7343)],
            15: [(20273, 14687), (20274, 14687), (20272, 14687)]
        },
        neighborhood_ids=["610012216", "610012217", "610012221", "610012263"]
    )
}

@dataclass
class EnhancedProvinceConfig:
    """Enhanced province configuration with browser traffic data"""
    name: str
    tile_server_name: str
    priority: int
    approximate_bbox: Tuple[float, float, float, float]
    browser_pattern: Optional[BrowserTrafficPattern] = None
    estimated_population: Optional[int] = None
    economic_importance: int = 1
    suhail_metrics_url: Optional[str] = None

@dataclass
class ParcelEnrichmentData:
    """Enrichment data from additional APIs"""
    parcel_id: str
    neighborhood_id: Optional[str] = None
    neighborhood_name: Optional[str] = None
    land_use_group: Optional[str] = None
    transactions_count: int = 0
    price_per_meter: Optional[float] = None
    growth_indicator: Optional[str] = None

@dataclass
class EnhancedDiscoveryResult:
    """Enhanced discovery result with multi-zoom analysis"""
    province_config: EnhancedProvinceConfig
    discovery_grids: List[DiscoveryGrid]
    total_parcels: int
    optimal_zoom: int
    data_hotspots: List[Tuple[int, int, int]]  # (z, x, y) coordinates
    neighborhood_data: Dict[str, dict] = None
    has_data: bool = False
    error_message: Optional[str] = None

# --- Enhanced Province Configurations ---
ENHANCED_PROVINCES = {
    "al_qassim": EnhancedProvinceConfig(
        name="Al_Qassim",
        tile_server_name="al_qassim",
        priority=1,  # Promoted due to browser traffic discovery
        approximate_bbox=(43.0, 25.5, 45.0, 27.5),
        browser_pattern=BROWSER_TRAFFIC_PATTERNS["al_qassim"],
        estimated_population=1_400_000,
        economic_importance=4,
        suhail_metrics_url="https://www.suhail.ai/Al_Qassim/metrics"
    ),
    "riyadh": EnhancedProvinceConfig(
        name="Riyadh",
        tile_server_name="riyadh",
        priority=2,
        approximate_bbox=(46.265364184769595, 23.986904579297715, 47.342260256150155, 25.781380632818795),
        estimated_population=8_000_000,
        economic_importance=5,
        suhail_metrics_url="https://www.suhail.ai/Riyadh/metrics"
    ),
    "madinah": EnhancedProvinceConfig(
        name="Madinah", 
        tile_server_name="al_madenieh",
        priority=3,
        approximate_bbox=(39.4133787747582, 24.091386951345967, 39.90345597984938, 24.91057558068701),
        estimated_population=2_200_000,
        economic_importance=4,
        suhail_metrics_url="https://www.suhail.ai/Madinah/metrics"
    ),
    "eastern": EnhancedProvinceConfig(
        name="Eastern",
        tile_server_name="eastern_region", 
        priority=4,
        approximate_bbox=(49.811760072324375, 25.91230398310188, 50.27967299061834, 26.682884502427413),
        estimated_population=5_000_000,
        economic_importance=4,
        suhail_metrics_url="https://www.suhail.ai/Eastern/metrics"
    ),
    "makkah": EnhancedProvinceConfig(
        name="Makkah",
        tile_server_name="makkah_region",
        priority=5,
        approximate_bbox=(38.925834, 20.827453, 39.606465, 22.357147),
        estimated_population=8_500_000,
        economic_importance=5, 
        suhail_metrics_url="https://www.suhail.ai/Makkah/metrics"
    ),
    "asir": EnhancedProvinceConfig(
        name="Asir",
        tile_server_name="asir_region",
        priority=6,
        approximate_bbox=(41.214223, 17.366667, 44.440789, 20.80266),
        browser_pattern=BROWSER_TRAFFIC_PATTERNS["asir"],
        estimated_population=2_200_000,
        economic_importance=3,
        suhail_metrics_url="https://www.suhail.ai/Asir/metrics"
    )
}

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")

async def fetch_neighborhood_data(neighborhood_id: str, growth_rate_type: int = 3) -> Optional[dict]:
    """Fetch neighborhood land metrics data"""
    url = f"https://api2.suhail.ai/api/mapMetrics/landMetrics?neighborhoodId={neighborhood_id}&growthRateType={growth_rate_type}"
    
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") and data.get("data"):
                return data["data"]
                
    except Exception as e:
        logging.debug(f"Failed to fetch neighborhood data for {neighborhood_id}: {e}")
    
    return None

async def fetch_parcel_transactions(parcel_object_id: str) -> Optional[dict]:
    """Fetch transaction data for a specific parcel"""
    url = f"https://api2.suhail.ai/transactions?parcelObjectId={parcel_object_id}"
    
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logging.debug(f"Failed to fetch transactions for parcel {parcel_object_id}: {e}")
    
    return None

def generate_multi_zoom_grid(bbox: Tuple[float, float, float, float], 
                           zoom_levels: List[int], 
                           grid_size: int = 3) -> Dict[int, List[Tuple[int, int, int]]]:
    """Generate discovery grids for multiple zoom levels"""
    west, south, east, north = bbox
    center_lon, center_lat = (west + east) / 2, (south + north) / 2
    
    grids = {}
    
    for zoom in zoom_levels:
        # Get center tile
        center_tile = mercantile.tile(center_lon, center_lat, zoom)
        
        # Generate surrounding grid
        tiles = []
        offset = grid_size // 2
        
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                x = center_tile.x + dx
                y = center_tile.y + dy
                if x >= 0 and y >= 0 and x < 2**zoom and y < 2**zoom:
                    tiles.append((zoom, x, y))
        
        grids[zoom] = tiles
    
    return grids

async def download_and_analyze_tile(province_name: str, tile_server: str, 
                                  tile_coords: Tuple[int, int, int]) -> Tuple[Optional[bytes], int, List]:
    """Download and analyze a single tile"""
    z, x, y = tile_coords
    url = f"https://tiles.suhail.ai/maps/{tile_server}/{z}/{x}/{y}.vector.pbf"
    
    try:
        async with httpx.AsyncClient(headers=HEADERS) as client:
            response = await client.get(url, timeout=20)
            response.raise_for_status()
            
            tile_size = len(response.content)
            
            if tile_size < MIN_TILE_SIZE_BYTES:
                return None, 0, []
            
            # Decode and count parcels
            try:
                decoder = MVTDecoder()
                gdfs = decoder.decode_to_gdf(response.content, z, x, y, layers=[TARGET_LAYER])
                parcels_gdf = gdfs.get(TARGET_LAYER)
                
                if parcels_gdf is not None and not parcels_gdf.empty:
                    parcel_count = len(parcels_gdf)
                    # Extract parcel IDs if available
                    parcel_ids = []
                    if 'object_id' in parcels_gdf.columns:
                        parcel_ids = parcels_gdf['object_id'].tolist()
                    elif 'id' in parcels_gdf.columns:
                        parcel_ids = parcels_gdf['id'].tolist()
                    
                    return response.content, parcel_count, parcel_ids
                    
            except Exception as e:
                logging.debug(f"Failed to decode tile {tile_coords}: {e}")
            
            return response.content, 0, []
            
    except Exception as e:
        logging.debug(f"Failed to download tile {tile_coords}: {e}")
        return None, 0, []

async def enhanced_province_discovery(config: EnhancedProvinceConfig) -> EnhancedDiscoveryResult:
    """Enhanced province discovery with multi-zoom sampling"""
    logging.info(f"\n🔍 Enhanced discovery for {config.name}")
    
    discovery_grids = []
    total_parcels = 0
    data_hotspots = []
    neighborhood_data = {}
    
    # Use browser traffic pattern if available
    if config.browser_pattern:
        logging.info(f"Using browser traffic pattern for {config.name}")
        zoom_grids = config.browser_pattern.zoom_grids
        
        # Fetch neighborhood data in parallel
        if config.browser_pattern.neighborhood_ids:
            logging.info(f"Fetching data for {len(config.browser_pattern.neighborhood_ids)} neighborhoods")
            neighborhood_tasks = [
                fetch_neighborhood_data(nid) 
                for nid in config.browser_pattern.neighborhood_ids
            ]
            neighborhood_results = await asyncio.gather(*neighborhood_tasks, return_exceptions=True)
            
            for nid, result in zip(config.browser_pattern.neighborhood_ids, neighborhood_results):
                if isinstance(result, dict):
                    neighborhood_data[nid] = result
                    
    else:
        # Generate standard multi-zoom grid
        logging.info(f"Generating multi-zoom grid for {config.name}")
        zoom_grids = generate_multi_zoom_grid(
            config.approximate_bbox, 
            DISCOVERY_ZOOM_RANGE
        )
    
    # Process each zoom level
    for zoom in sorted(zoom_grids.keys()):
        if config.browser_pattern:
            # Browser pattern already has (x, y) tuples
            grid_tiles = [(zoom, x, y) for x, y in zoom_grids[zoom]]
        else:
            # Generated grid has (z, x, y) tuples
            grid_tiles = zoom_grids[zoom]
        
        logging.info(f"Testing zoom {zoom} with {len(grid_tiles)} tiles")
        
        # Download tiles in parallel (with rate limiting)
        tasks = []
        for i, tile_coords in enumerate(grid_tiles):
            if i > 0 and i % 5 == 0:  # Rate limiting
                await asyncio.sleep(0.5)
            
            tasks.append(download_and_analyze_tile(
                config.name, config.tile_server_name, tile_coords
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        grid_parcels = 0
        grid_size = 0
        
        for tile_coords, result in zip(grid_tiles, results):
            if isinstance(result, tuple) and result[0] is not None:
                _, parcel_count, parcel_ids = result
                if parcel_count > 0:
                    data_hotspots.append(tile_coords)
                    grid_parcels += parcel_count
                    grid_size += len(result[0])
        
        grid_result = DiscoveryGrid(
            zoom=zoom,
            tiles=grid_tiles,
            data_found=grid_parcels > 0,
            total_parcels=grid_parcels,
            total_size_bytes=grid_size
        )
        
        discovery_grids.append(grid_result)
        total_parcels += grid_parcels
        
        logging.info(f"Zoom {zoom}: {grid_parcels} parcels, {grid_size/1024:.1f}KB")
    
    # Find optimal zoom level
    optimal_zoom = max(
        (grid for grid in discovery_grids if grid.data_found),
        key=lambda g: g.total_parcels,
        default=discovery_grids[0] if discovery_grids else None
    )
    
    optimal_zoom_level = optimal_zoom.zoom if optimal_zoom else DISCOVERY_ZOOM_RANGE[0]
    
    result = EnhancedDiscoveryResult(
        province_config=config,
        discovery_grids=discovery_grids,
        total_parcels=total_parcels,
        optimal_zoom=optimal_zoom_level,
        data_hotspots=data_hotspots,
        neighborhood_data=neighborhood_data,
        has_data=total_parcels > 0
    )
    
    logging.info(f"✅ {config.name}: {total_parcels} parcels across {len(data_hotspots)} hotspots")
    
    return result

def save_enhanced_results(results: List[EnhancedDiscoveryResult], 
                        output_dir: str = "enhanced_discovery_results"):
    """Save enhanced discovery results"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    summary = {
        "timestamp": time.time(),
        "provinces": [],
        "total_parcels": sum(r.total_parcels for r in results),
        "total_hotspots": sum(len(r.data_hotspots) for r in results)
    }
    
    for result in results:
        province_data = {
            "name": result.province_config.name,
            "server": result.province_config.tile_server_name,
            "total_parcels": result.total_parcels,
            "optimal_zoom": result.optimal_zoom,
            "data_hotspots": result.data_hotspots,
            "zoom_analysis": [
                {
                    "zoom": grid.zoom,
                    "parcels": grid.total_parcels,
                    "size_kb": grid.total_size_bytes / 1024,
                    "data_found": grid.data_found
                }
                for grid in result.discovery_grids
            ],
            "neighborhood_data": result.neighborhood_data or {}
        }
        
        summary["provinces"].append(province_data)
        
        # Save individual province results
        province_file = output_path / f"{result.province_config.tile_server_name}_enhanced.json"
        with open(province_file, 'w') as f:
            json.dump(province_data, f, indent=2)
        
        logging.info(f"Saved {result.province_config.name} data to {province_file}")
    
    # Save summary
    summary_file = output_path / "enhanced_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logging.info(f"Enhanced discovery complete: {summary['total_parcels']} parcels, {summary['total_hotspots']} hotspots")

@app.command()
def enhanced_discover(
    provinces: Optional[List[str]] = typer.Argument(
        default=None, 
        help="Province names to discover"
    ),
    output_dir: str = typer.Option(
        "enhanced_discovery_results", 
        "--output", "-o",
        help="Output directory"
    )
):
    """Enhanced province discovery with multi-zoom analysis and API integration"""
    
    async def main():
        # Use default if no provinces specified
        target_provinces = provinces if provinces else ["al_qassim"]
        
        configs = [
            ENHANCED_PROVINCES[name] 
            for name in target_provinces 
            if name in ENHANCED_PROVINCES
        ]
        
        if not configs:
            logging.error(f"No valid provinces found. Available: {list(ENHANCED_PROVINCES.keys())}")
            return
        
        logging.info(f"🚀 Starting enhanced discovery for {len(configs)} provinces")
        
        results = []
        for config in configs:
            result = await enhanced_province_discovery(config)
            results.append(result)
            
            # Small delay between provinces
            await asyncio.sleep(2)
        
        save_enhanced_results(results, output_dir)
    
    asyncio.run(main())

@app.command()
def browser_pattern():
    """Show known browser traffic patterns"""
    for province, pattern in BROWSER_TRAFFIC_PATTERNS.items():
        print(f"\n🌍 {province.upper()} Browser Traffic Pattern:")
        for zoom, coordinates in pattern.zoom_grids.items():
            print(f"  z{zoom}: {len(coordinates)} tiles")
        if pattern.neighborhood_ids:
            print(f"  Neighborhoods: {len(pattern.neighborhood_ids)} IDs")

if __name__ == "__main__":
    app() 
