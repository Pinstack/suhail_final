#!/usr/bin/env python3
"""
Comprehensive Market Analysis by Building Type
"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json
from datetime import datetime

# Add dotenv support
from dotenv import load_dotenv
load_dotenv()

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from meshic_pipeline.persistence.db import get_db_engine
from sqlalchemy import text


def analyze_market_by_building_type():
    """Comprehensive market analysis by building type."""
    engine = get_db_engine()
    
    print("🏢 COMPREHENSIVE MARKET ANALYSIS BY BUILDING TYPE")
    print("=" * 60)
    print()
    
    with engine.connect() as conn:
        # 1. OVERALL MARKET SUMMARY
        print("📊 OVERALL MARKET SUMMARY")
        print("-" * 30)
        
        # Total parcels by land use
        result = conn.execute(text("""
            SELECT 
                landuseagroup,
                COUNT(*) as parcel_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM parcels 
            WHERE landuseagroup IS NOT NULL
            GROUP BY landuseagroup
            ORDER BY parcel_count DESC
        """))
        
        print("Parcels by Land Use Type:")
        for row in result:
            print(f"  {row.landuseagroup}: {row.parcel_count:,} parcels ({row.percentage}%)")
        
        print()
        
        # 2. TRANSACTION ANALYSIS BY BUILDING TYPE
        print("💰 TRANSACTION ANALYSIS BY BUILDING TYPE")
        print("-" * 40)
        
        # Transactions with building type info
        result = conn.execute(text("""
            SELECT 
                p.landuseagroup,
                COUNT(t.transaction_id) as transaction_count,
                AVG(t.transaction_price) as avg_transaction_price,
                MIN(t.transaction_price) as min_transaction_price,
                MAX(t.transaction_price) as max_transaction_price,
                AVG(t.price_of_meter) as avg_price_per_meter,
                MIN(t.price_of_meter) as min_price_per_meter,
                MAX(t.price_of_meter) as max_price_per_meter,
                AVG(t.area) as avg_area
            FROM transactions t
            JOIN parcels p ON t.parcel_objectid = p.parcel_objectid
            WHERE p.landuseagroup IS NOT NULL
            GROUP BY p.landuseagroup
            ORDER BY transaction_count DESC
        """))
        
        print("Transaction Statistics by Building Type:")
        print(f"{'Building Type':<25} {'Count':<8} {'Avg Price':<12} {'Avg/m²':<10} {'Avg Area':<10}")
        print("-" * 75)
        
        for row in result:
            print(f"{row.landuseagroup:<25} {row.transaction_count:<8} {row.avg_transaction_price:<12,.0f} {row.avg_price_per_meter:<10,.0f} {row.avg_area:<10,.0f}")
        
        print()
        
        # 3. PRICE METRICS ANALYSIS BY BUILDING TYPE
        print("📈 PRICE METRICS ANALYSIS BY BUILDING TYPE")
        print("-" * 45)
        
        result = conn.execute(text("""
            SELECT 
                p.landuseagroup,
                COUNT(pm.metric_id) as metric_count,
                AVG(pm.average_price_of_meter) as avg_price_per_meter,
                MIN(pm.average_price_of_meter) as min_price_per_meter,
                MAX(pm.average_price_of_meter) as max_price_per_meter,
                COUNT(DISTINCT pm.metrics_type) as metric_types
            FROM parcel_price_metrics pm
            JOIN parcels p ON pm.parcel_objectid = p.parcel_objectid
            WHERE p.landuseagroup IS NOT NULL
            GROUP BY p.landuseagroup
            ORDER BY metric_count DESC
        """))
        
        print("Price Metrics by Building Type:")
        print(f"{'Building Type':<25} {'Metrics':<8} {'Avg/m²':<12} {'Min/m²':<10} {'Max/m²':<10} {'Types':<6}")
        print("-" * 80)
        
        for row in result:
            print(f"{row.landuseagroup:<25} {row.metric_count:<8} {row.avg_price_per_meter:<12,.0f} {row.min_price_per_meter:<10,.0f} {row.max_price_per_meter:<10,.0f} {row.metric_types:<6}")
        
        print()
        
        # 4. ZONING ANALYSIS BY BUILDING TYPE
        print("🏗️ ZONING ANALYSIS BY BUILDING TYPE")
        print("-" * 35)
        
        result = conn.execute(text("""
            SELECT 
                landuseagroup,
                zoning_color,
                COUNT(*) as parcel_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY landuseagroup), 2) as percentage
            FROM parcels 
            WHERE landuseagroup IS NOT NULL AND zoning_color IS NOT NULL
            GROUP BY landuseagroup, zoning_color
            ORDER BY landuseagroup, parcel_count DESC
        """))
        
        current_group = None
        for row in result:
            if current_group != row.landuseagroup:
                if current_group is not None:
                    print()
                current_group = row.landuseagroup
                print(f"{row.landuseagroup}:")
            print(f"  {row.zoning_color}: {row.parcel_count:,} parcels ({row.percentage}%)")
        
        print()
        
        # 5. SUBDIVISION ANALYSIS BY BUILDING TYPE
        print("📍 SUBDIVISION ANALYSIS BY BUILDING TYPE")
        print("-" * 40)
        
        result = conn.execute(text("""
            SELECT 
                landuseagroup,
                subdivision_no,
                COUNT(*) as parcel_count,
                AVG(price_of_meter) as avg_price_per_meter
            FROM parcels 
            WHERE landuseagroup IS NOT NULL AND subdivision_no IS NOT NULL
            GROUP BY landuseagroup, subdivision_no
            HAVING COUNT(*) >= 10
            ORDER BY landuseagroup, parcel_count DESC
        """))
        
        current_group = None
        for row in result:
            if current_group != row.landuseagroup:
                if current_group is not None:
                    print()
                current_group = row.landuseagroup
                print(f"{row.landuseagroup} - Top Subdivisions:")
            print(f"  {row.subdivision_no}: {row.parcel_count:,} parcels, avg {row.avg_price_per_meter:,.0f} SAR/m²")
        
        print()
        
        # 6. TRANSACTION TIMELINE ANALYSIS
        print("📅 TRANSACTION TIMELINE ANALYSIS")
        print("-" * 35)
        
        result = conn.execute(text("""
            SELECT 
                p.landuseagroup,
                EXTRACT(YEAR FROM t.transaction_date) as year,
                EXTRACT(MONTH FROM t.transaction_date) as month,
                COUNT(*) as transaction_count,
                AVG(t.transaction_price) as avg_price,
                AVG(t.price_of_meter) as avg_price_per_meter
            FROM transactions t
            JOIN parcels p ON t.parcel_objectid = p.parcel_objectid
            WHERE p.landuseagroup IS NOT NULL AND t.transaction_date IS NOT NULL
            GROUP BY p.landuseagroup, EXTRACT(YEAR FROM t.transaction_date), EXTRACT(MONTH FROM t.transaction_date)
            ORDER BY p.landuseagroup, year DESC, month DESC
        """))
        
        current_group = None
        for row in result:
            if current_group != row.landuseagroup:
                if current_group is not None:
                    print()
                current_group = row.landuseagroup
                print(f"{row.landuseagroup} - Transaction Timeline:")
            year = int(row.year) if row.year else 0
            month = int(row.month) if row.month else 0
            print(f"  {year}-{month:02d}: {row.transaction_count} transactions, avg {row.avg_price:,.0f} SAR, {row.avg_price_per_meter:,.0f} SAR/m²")
        
        print()
        
        # 7. MARKET INSIGHTS AND RECOMMENDATIONS
        print("💡 MARKET INSIGHTS AND RECOMMENDATIONS")
        print("-" * 45)
        
        # Get key statistics for insights
        result = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT p.parcel_objectid) as total_parcels,
                COUNT(DISTINCT t.transaction_id) as total_transactions,
                COUNT(DISTINCT pm.metric_id) as total_metrics,
                AVG(t.transaction_price) as overall_avg_price,
                AVG(t.price_of_meter) as overall_avg_price_per_meter
            FROM parcels p
            LEFT JOIN transactions t ON p.parcel_objectid = t.parcel_objectid
            LEFT JOIN parcel_price_metrics pm ON p.parcel_objectid = pm.parcel_objectid
        """))
        
        stats = result.fetchone()
        
        print(f"📊 Market Overview:")
        print(f"  • Total Parcels: {stats.total_parcels:,}")
        print(f"  • Total Transactions: {stats.total_transactions:,}")
        print(f"  • Total Price Metrics: {stats.total_metrics:,}")
        print(f"  • Overall Average Transaction Price: {stats.overall_avg_price:,.0f} SAR")
        print(f"  • Overall Average Price per m²: {stats.overall_avg_price_per_meter:,.0f} SAR")
        
        print()
        print("🎯 Key Insights:")
        print("  • Residential properties dominate the market")
        print("  • Mixed-use properties show significant presence")
        print("  • Commercial/industrial properties have limited transaction data")
        print("  • Price per square meter varies significantly by building type")
        print("  • Zoning distribution shows market segmentation")
        
        print()
        print("📋 Recommendations:")
        print("  • Focus on residential market analysis for primary insights")
        print("  • Expand data collection for commercial properties")
        print("  • Monitor mixed-use property trends")
        print("  • Analyze zoning changes and their impact on prices")
        print("  • Consider temporal analysis for market trend identification")


def main():
    """Main analysis function."""
    try:
        analyze_market_by_building_type()
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 