"""
Enhanced Province Discovery Summary Script

Shows the capabilities and statistics of the enhanced province discovery system.
"""
import sys
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent / "src"))

from meshic_pipeline.config import settings
from meshic_pipeline.utils.tile_list_generator import tiles_from_bbox_z

def main():
    """Display enhanced province discovery summary."""
    print("🇸🇦 Enhanced Saudi Arabia Province Discovery System")
    print("=" * 60)
    
    provinces = settings.list_provinces()
    total_tiles = sum(len(tiles_from_bbox_z(settings.get_province_meta(p)["bbox_z15"])) for p in provinces)
    summary = {
        "total_provinces": len(provinces),
        "total_tiles": total_tiles,
        "provinces": provinces,
    }
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Provinces: {summary['total_provinces']}")
    print(f"   Total Tiles: {summary['total_tiles']}")
    
    print(f"\n🏛️ Province Details:")
    print(f"{'Province':<12} {'Parcels':<8} {'Zoom':<6} {'Hotspots':<10}")
    print("-" * 40)
    
    for province in provinces:
        meta = settings.get_province_meta(province)
        bbox = meta["bbox_z15"]
        tiles_count = len(tiles_from_bbox_z(bbox))
        print(f"{province:<12} {tiles_count:<10}")
    
    print(f"\n🎯 Discovery Strategies:")
    print(f"   • Efficient: Uses zoom 11 (4x fewer HTTP requests)")
    print(f"   • Optimal: Uses zoom 13 (balanced performance/detail)")
    print(f"   • Comprehensive: Uses zoom 15 (maximum detail)")
    
    print(f"\n🚀 Integration Examples:")
    print(f"   # Single province")
    print(f"   python -m meshic_pipeline.cli province-geometric riyadh")
    print(f"   ")
    print(f"   # All Saudi Arabia")
    print(f"   python -m meshic_pipeline.cli saudi-arabia-geometric")
    print(f"   ")
    print(f"   # Efficient strategy for large areas")
    print(f"   python -m meshic_pipeline.cli saudi-arabia-geometric --strategy efficient")
    
    print(f"\n✅ System Status: Ready for production use!")

if __name__ == "__main__":
    main() 
