#!/usr/bin/env python3
"""
Export spatial data from the database to GeoJSON format.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add dotenv support
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meshic_pipeline.persistence.db import get_db_engine
from sqlalchemy import text


def export_table_to_geojson(table_name: str, output_file: str, limit: int = None) -> Dict[str, Any]:
    """
    Export a spatial table to GeoJSON format.
    
    Args:
        table_name: Name of the table to export
        output_file: Path to output GeoJSON file
        limit: Optional limit on number of features to export
    
    Returns:
        Dictionary with export statistics
    """
    engine = get_db_engine()
    
    # Check if table has geometry column
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND table_schema = 'public'
            AND column_name IN ('geometry', 'geom')
        """), {"table_name": table_name})
        
        geom_columns = [row[0] for row in result]
        
        if not geom_columns:
            print(f"⚠️  Table {table_name} has no geometry column, skipping...")
            return {"table": table_name, "status": "skipped", "reason": "no_geometry"}
        
        geom_column = geom_columns[0]
        
        # Get all columns
        result = conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = :table_name 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """), {"table_name": table_name})
        
        columns = [(row[0], row[1]) for row in result]
        
        # Build query
        select_cols = []
        for col_name, col_type in columns:
            if col_name == geom_column:
                select_cols.append(f"ST_AsGeoJSON({col_name}) as geometry")
            else:
                select_cols.append(col_name)
        
        query = f"""
            SELECT {', '.join(select_cols)}
            FROM {table_name}
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        # Execute query
        result = conn.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            print(f"⚠️  Table {table_name} is empty, skipping...")
            return {"table": table_name, "status": "skipped", "reason": "empty"}
        
        # Convert to GeoJSON
        features = []
        for row in rows:
            feature = {
                "type": "Feature",
                "geometry": json.loads(row.geometry) if row.geometry else None,
                "properties": {}
            }
            
            # Add all non-geometry properties
            for i, (col_name, col_type) in enumerate(columns):
                if col_name != geom_column:
                    value = row[i]
                    # Handle special data types
                    if hasattr(value, 'isoformat'):  # datetime
                        value = value.isoformat()
                    feature["properties"][col_name] = value
            
            features.append(feature)
        
        geojson = {
            "type": "FeatureCollection",
            "features": features
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(geojson, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Exported {len(features)} features from {table_name} to {output_file}")
        
        return {
            "table": table_name,
            "status": "success",
            "features": len(features),
            "file": output_file
        }


def main():
    """Main export function."""
    # Tables to export (spatial tables with data)
    tables_to_export = [
        "neighborhoods",
        "subdivisions", 
        "parcels",
        "metro_lines",
        "metro_stations",
        "bus_lines",
        "riyadh_bus_stations",
        "qi_population_metrics",
        "qi_stripes"
    ]
    
    # Create output directory
    output_dir = Path("exports")
    output_dir.mkdir(exist_ok=True)
    
    print("🚀 Starting GeoJSON export...")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print()
    
    results = []
    
    for table_name in tables_to_export:
        output_file = output_dir / f"{table_name}.geojson"
        result = export_table_to_geojson(table_name, str(output_file))
        results.append(result)
        print()
    
    # Summary
    print("📊 Export Summary:")
    print("=" * 50)
    
    successful = [r for r in results if r["status"] == "success"]
    skipped = [r for r in results if r["status"] == "skipped"]
    
    if successful:
        print(f"✅ Successfully exported {len(successful)} tables:")
        for result in successful:
            print(f"   - {result['table']}: {result['features']} features → {result['file']}")
    
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} tables:")
        for result in skipped:
            print(f"   - {result['table']}: {result['reason']}")
    
    print()
    print(f"🎉 Export complete! Files saved in: {output_dir.absolute()}")


if __name__ == "__main__":
    main() 