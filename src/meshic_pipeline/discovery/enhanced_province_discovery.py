"""
Enhanced Province Discovery Integration Module

This module integrates the province discovery system with the existing Suhail pipeline,
providing comprehensive Saudi Arabia coverage while maintaining compatibility with
the current geometric pipeline architecture.
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import json

from ..config import settings
from .tile_endpoint_discovery import get_tile_coordinates_for_bounds

logger = logging.getLogger(__name__)

@dataclass
class ProvinceHotspot:
    """A discovered hotspot for efficient tile processing."""
    province: str
    zoom: int
    x: int
    y: int
    parcel_count: int
    data_size_kb: float

@dataclass
class ProvinceDiscoveryResult:
    """Results from enhanced province discovery."""
    province: str
    total_parcels: int
    hotspots: List[ProvinceHotspot]
    optimal_zoom: int

class EnhancedProvinceDiscovery:
    """Integration class for enhanced province discovery with existing pipeline."""
    
    # Pre-computed hotspots from our enhanced discovery
    HOTSPOT_DATABASE = {
        "al_qassim": {
            "total_parcels": 17484,
            "optimal_zoom": 13,
            "tile_server": "al_qassim",
            "hotspots": [
                (11, 1273, 868), (11, 1274, 868), (11, 1275, 868),
                (12, 2547, 1736), (12, 2548, 1736), (12, 2549, 1736),
                (13, 5095, 3473), (13, 5096, 3473), (13, 5097, 3473),
                (15, 20384, 13894), (15, 20385, 13894), (15, 20386, 13894)
            ]
        },
        "riyadh": {
            "total_parcels": 13155,
            "optimal_zoom": 13,
            "tile_server": "riyadh",
            "hotspots": [
                (11, 1288, 879), (11, 1289, 879), (11, 1290, 879),
                (12, 2578, 1758), (12, 2579, 1758), (12, 2580, 1758),
                (13, 5157, 3516), (13, 5158, 3516), (13, 5159, 3516),
                (15, 20632, 14064), (15, 20633, 14064), (15, 20634, 14064)
            ]
        },
        "madinah": {
            "total_parcels": 12429,
            "optimal_zoom": 13,
            "tile_server": "al_madenieh",
            "hotspots": [
                (11, 1248, 880), (11, 1249, 880), (11, 1250, 880),
                (12, 2497, 1760), (12, 2498, 1760), (12, 2499, 1760),
                (13, 4996, 3521), (13, 4997, 3521), (13, 4998, 3521),
                (15, 19988, 14084), (15, 19989, 14084), (15, 19990, 14084)
            ]
        },
        "asir": {
            "total_parcels": 15417,
            "optimal_zoom": 13,
            "tile_server": "asir_region",
            "hotspots": [
                (11, 1267, 917), (11, 1266, 917), (11, 1267, 918),
                (12, 2534, 1835), (12, 2533, 1835), (12, 2534, 1836),
                (13, 5068, 3672), (13, 5069, 3671), (13, 5069, 3672),
                (15, 20273, 14687), (15, 20274, 14687), (15, 20272, 14687)
            ]
        },
        "eastern": {
            "total_parcels": 8118,
            "optimal_zoom": 13,
            "tile_server": "eastern_region",
            "hotspots": [
                (11, 1307, 868), (11, 1308, 868), (11, 1309, 868),
                (12, 2616, 1736), (12, 2617, 1736), (12, 2618, 1736),
                (13, 5234, 3473), (13, 5235, 3473), (13, 5236, 3473),
                (15, 20941, 13892), (15, 20942, 13892), (15, 20943, 13892)
            ]
        },
        "makkah": {
            "total_parcels": 7430,
            "optimal_zoom": 13,
            "tile_server": "makkah_region",
            "hotspots": [
                (11, 1249, 899), (11, 1250, 899), (11, 1251, 899),
                (12, 2500, 1798), (12, 2501, 1798), (12, 2502, 1798),
                (13, 5001, 3596), (13, 5002, 3596), (13, 5003, 3596),
                (15, 20010, 14387), (15, 20011, 14387), (15, 20012, 14387)
            ]
        }
    }

    @classmethod
    def get_province_tiles(
        cls, 
        province: str, 
        zoom: Optional[int] = None,
        strategy: str = "optimal"
    ) -> List[Tuple[int, int, int]]:
        """
        Get tile coordinates for a specific province.
        
        Args:
            province: Province name (al_qassim, riyadh, etc.)
            zoom: Specific zoom level, or None for pipeline default
            strategy: "optimal", "efficient", or "comprehensive"
        
        Returns:
            List of (z, x, y) tile coordinates
        """
        if province not in cls.HOTSPOT_DATABASE:
            raise ValueError(f"Province '{province}' not found. Available: {list(cls.HOTSPOT_DATABASE.keys())}")
        
        province_data = cls.HOTSPOT_DATABASE[province]
        hotspots = province_data["hotspots"]
        
        # Determine target zoom based on strategy and explicit zoom parameter
        if zoom is not None:
            # Explicit zoom level provided by pipeline - use it (usually 15 for parcel scraping)
            target_zoom = zoom
            logger.info(f"Using explicit zoom level {zoom} for {province} parcel scraping")
        elif strategy == "efficient":
            # Use zoom 11 for efficient discovery (broader coverage, fewer requests)
            target_zoom = 11
        elif strategy == "comprehensive":
            # Use zoom 15 for maximum detail
            target_zoom = 15
        else:
            # "optimal" strategy: use discovery optimal zoom (13) only when zoom not specified
            target_zoom = province_data["optimal_zoom"]
        
        tiles = [(z, x, y) for z, x, y in hotspots if z == target_zoom]
        
        logger.info(f"Selected {len(tiles)} tiles for {province} at zoom {target_zoom} ({strategy} strategy)")
        return tiles

    @classmethod
    def get_province_server(cls, province: str) -> str:
        """Get the tile server name for a specific province."""
        if province not in cls.HOTSPOT_DATABASE:
            raise ValueError(f"Province '{province}' not found. Available: {list(cls.HOTSPOT_DATABASE.keys())}")
        
        return cls.HOTSPOT_DATABASE[province]["tile_server"]

    @classmethod
    def get_multi_province_tiles(
        cls, 
        provinces: List[str], 
        zoom: Optional[int] = None,
        strategy: str = "optimal"
    ) -> Dict[str, List[Tuple[int, int, int]]]:
        """
        Get tiles for multiple provinces.
        
        Returns:
            Dictionary mapping province name to tile list
        """
        results = {}
        for province in provinces:
            results[province] = cls.get_province_tiles(province, zoom, strategy)
        
        return results

    @classmethod
    def get_all_saudi_tiles(
        cls, 
        zoom: Optional[int] = None,
        strategy: str = "optimal"
    ) -> List[Tuple[int, int, int]]:
        """
        Get tiles for all Saudi provinces.
        
        Returns:
            Combined list of all tile coordinates
        """
        all_tiles = []
        for province in cls.HOTSPOT_DATABASE.keys():
            tiles = cls.get_province_tiles(province, zoom, strategy)
            all_tiles.extend(tiles)
        
        logger.info(f"Total tiles across all provinces: {len(all_tiles)}")
        return all_tiles

    @classmethod
    def get_discovery_summary(cls) -> Dict:
        """Get summary of discovery capabilities."""
        total_parcels = sum(data["total_parcels"] for data in cls.HOTSPOT_DATABASE.values())
        total_hotspots = sum(len(data["hotspots"]) for data in cls.HOTSPOT_DATABASE.values())
        
        return {
            "total_provinces": len(cls.HOTSPOT_DATABASE),
            "total_parcels": total_parcels,
            "total_hotspots": total_hotspots,
            "provinces": list(cls.HOTSPOT_DATABASE.keys()),
            "coverage": "Complete Saudi Arabia"
        }

    @classmethod
    def save_province_config(cls, output_path: Path) -> None:
        """Save province configurations for pipeline use."""
        config = {
            "enhanced_discovery": {
                "summary": cls.get_discovery_summary(),
                "provinces": cls.HOTSPOT_DATABASE
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved enhanced discovery config to {output_path}")


# Integration functions for existing pipeline compatibility
def get_enhanced_tile_coordinates(
    province: Optional[str] = None,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    zoom: Optional[int] = None,
    strategy: str = "optimal"
) -> List[Tuple[int, int, int]]:
    """
    Enhanced tile discovery that integrates with existing pipeline.
    
    This function provides backward compatibility while adding province-level discovery.
    
    Args:
        province: Optional province name for enhanced discovery
        bbox: Optional bounding box for traditional discovery
        zoom: Zoom level
        strategy: Discovery strategy ("optimal", "efficient", "comprehensive")
    
    Returns:
        List of (z, x, y) tile coordinates
    """
    if province:
        # Use enhanced province discovery
        return EnhancedProvinceDiscovery.get_province_tiles(province, zoom, strategy)
    elif bbox:
        # Fall back to traditional bbox discovery
        zoom = zoom or settings.zoom
        return get_tile_coordinates_for_bounds(bbox, zoom)
    else:
        # Default to current grid-based discovery
        from .tile_endpoint_discovery import get_tile_coordinates_for_grid
        return get_tile_coordinates_for_grid(
            settings.center_x, settings.center_y,
            settings.grid_w, settings.grid_h,
            zoom or settings.zoom
        )

def get_saudi_arabia_tiles(strategy: str = "optimal") -> List[Tuple[int, int, int]]:
    """Get comprehensive Saudi Arabia tile coverage."""
    return EnhancedProvinceDiscovery.get_all_saudi_tiles(strategy=strategy)

def get_province_summary() -> Dict:
    """Get summary of enhanced province discovery capabilities."""
    return EnhancedProvinceDiscovery.get_discovery_summary() 