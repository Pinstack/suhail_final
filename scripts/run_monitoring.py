#!/usr/bin/env python3
"""
Enrichment Monitoring Script
Tracks enrichment status and helps identify when incremental updates are needed.
"""

import typer
import sys
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from meshic_pipeline.config import settings

app = typer.Typer()

@app.command()
def status():
    """Check current enrichment status."""
    engine = create_engine(str(settings.database_url))
    
    with engine.connect() as conn:
        # Basic counts
        total_parcels = conn.execute(text("SELECT COUNT(*) FROM public.parcels WHERE transaction_price > 0")).scalar()
        enriched_parcels = conn.execute(text("SELECT COUNT(*) FROM public.parcels WHERE enriched_at IS NOT NULL")).scalar()
        tx_count = conn.execute(text("SELECT COUNT(*) FROM public.transactions")).scalar()
        
        # Enrichment age analysis
        age_stats = conn.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE enriched_at >= NOW() - INTERVAL '1 day') as last_24h,
                COUNT(*) FILTER (WHERE enriched_at >= NOW() - INTERVAL '7 days') as last_7d,
                COUNT(*) FILTER (WHERE enriched_at >= NOW() - INTERVAL '30 days') as last_30d,
                COUNT(*) FILTER (WHERE enriched_at < NOW() - INTERVAL '30 days') as older_30d,
                MIN(enriched_at) as oldest_enrichment,
                MAX(enriched_at) as newest_enrichment
            FROM public.parcels 
            WHERE enriched_at IS NOT NULL
        """)).fetchone()
        
        print("🔍 ENRICHMENT STATUS REPORT")
        print("=" * 50)
        print(f"📊 Parcel Overview:")
        print(f"   • Total enrichable parcels: {total_parcels:,}")
        print(f"   • Enriched parcels: {enriched_parcels:,}")
        print(f"   • Unenriched parcels: {total_parcels - enriched_parcels:,}")
        print(f"   • Coverage: {(enriched_parcels/total_parcels)*100:.1f}%")
        print()
        print(f"📈 Transaction Data:")
        print(f"   • Total transactions: {tx_count:,}")
        print(f"   • Avg transactions per enriched parcel: {tx_count/max(enriched_parcels,1):.1f}")
        print()
        
        if age_stats and age_stats[0] is not None:
            print(f"⏰ Enrichment Freshness:")
            print(f"   • Last 24 hours: {age_stats[0]:,} parcels")
            print(f"   • Last 7 days: {age_stats[1]:,} parcels") 
            print(f"   • Last 30 days: {age_stats[2]:,} parcels")
            print(f"   • Older than 30 days: {age_stats[3]:,} parcels")
            print(f"   • Oldest enrichment: {age_stats[4]}")
            print(f"   • Newest enrichment: {age_stats[5]}")
            
            if age_stats[3] > 0:
                print(f"⚠️  RECOMMENDATION: Run incremental enrichment for {age_stats[3]:,} stale parcels")

@app.command()
def recommend():
    """Recommend next enrichment strategy."""
    engine = create_engine(str(settings.database_url))
    
    with engine.connect() as conn:
        # Check for new parcels that could be triggers (transaction_price > 0 but never enriched)
        trigger_parcels = conn.execute(text("""
            SELECT COUNT(*) FROM public.parcels p
            LEFT JOIN public.transactions t ON p.parcel_objectid = t.parcel_objectid
            WHERE p.transaction_price > 0 AND t.parcel_objectid IS NULL
        """)).scalar()
        
        # Check for unenriched parcels with transaction data
        total_enrichable = conn.execute(text("SELECT COUNT(*) FROM public.parcels WHERE transaction_price > 0")).scalar()
        already_enriched = conn.execute(text("SELECT COUNT(DISTINCT parcel_objectid) FROM public.transactions")).scalar()
        new_parcels = total_enrichable - already_enriched
        
        # Check for stale parcels (30+ days old)
        cutoff_30d = datetime.now() - timedelta(days=30)
        stale_30d = conn.execute(text("""
            SELECT COUNT(*) FROM public.parcels
            WHERE transaction_price > 0 
            AND (enriched_at IS NULL OR enriched_at < :cutoff_date)
        """), {"cutoff_date": cutoff_30d}).scalar()
        
        # Check for stale parcels (7+ days old) 
        cutoff_7d = datetime.now() - timedelta(days=7)
        stale_7d = conn.execute(text("""
            SELECT COUNT(*) FROM public.parcels
            WHERE transaction_price > 0 
            AND (enriched_at IS NULL OR enriched_at < :cutoff_date)
        """), {"cutoff_date": cutoff_7d}).scalar()
        
        print("🎯 INTELLIGENT ENRICHMENT RECOMMENDATIONS")
        print("=" * 60)
        
        # Priority analysis
        enrichment_coverage = (already_enriched / total_enrichable) * 100 if total_enrichable > 0 else 0
        
        print(f"📊 CURRENT STATUS:")
        print(f"   • Total enrichable parcels: {total_enrichable:,}")
        print(f"   • Already enriched: {already_enriched:,} ({enrichment_coverage:.1f}%)")
        print(f"   • Remaining to enrich: {new_parcels:,}")
        print()
        
        # Priority 1: Large number of unenriched parcels with transaction data
        if new_parcels > 10000:
            print(f"🚀 HIGHEST PRIORITY: {new_parcels:,} UNENRICHED PARCels WITH TRANSACTION DATA")
            print(f"   💡 Stage 1 geometric pipeline revealed {new_parcels:,} parcels with transaction_price > 0!")
            print(f"   Recommended: python scripts/run_enrichment_pipeline.py fast-enrich --batch-size 400")
            print("   → Leverages transaction_price field from MVT tiles for maximum efficiency")
            print()
        elif new_parcels > 1000:
            print(f"🆕 HIGH PRIORITY: {new_parcels:,} unenriched parcels found")
            print(f"   Recommended: python scripts/run_enrichment_pipeline.py fast-enrich --batch-size 300")
            print()
        
        # Priority 2: Incremental updates for already enriched parcels
        if stale_7d > 5000:
            print(f"⚠️  MEDIUM PRIORITY: {stale_7d:,} stale parcels (7+ days)")
            print(f"   💡 May have new transactions not yet captured")
            print(f"   Recommended: python scripts/run_enrichment_pipeline.py incremental-enrich --days-old 7")
            print()
        elif stale_30d > 1000:
            print(f"⏰ LOW PRIORITY: {stale_30d:,} stale parcels (30+ days)") 
            print(f"   Recommended: python scripts/run_enrichment_pipeline.py incremental-enrich --days-old 30")
            print()
        
        # System status
        if new_parcels == 0 and stale_7d < 100:
            print("✅ EXCELLENT: System is up to date!")
            print("   No immediate action needed")
            print("   Consider weekly incremental updates to catch new transactions")
            print()
        elif new_parcels < 100:
            print("✅ GOOD: Most parcels with transaction data are enriched")
            print(f"   Only {new_parcels:,} parcels remaining")
            print()
        
        # Strategic recommendations based on your insight
        print("🧠 OPTIMAL STRATEGY:")
        print("   💡 The most efficient method is 'delta-enrich', which only processes parcels with detected changes.")
        print()
        print("   🆕 RECOMMENDED WORKFLOW: DELTA ENRICHMENT (Maximum Precision):")
        print("      python scripts/run_enrichment_pipeline.py delta-enrich --auto-geometric")
        print("      → MVT-based change detection: Only enrich parcels with ACTUAL price changes")
        print("      → Detects: New parcels, price changes, market updates")
        print("      → Ultimate efficiency: Only processes parcels with proven changes")
        print()
        print("   💡 DELTA STRATEGY BENEFITS:")
        print("      • No false positives from time-based approaches")
        print("      • Real market signal detection")
        print("      • Eliminates unnecessary API calls")
        print("      • Perfect for automated daily or weekly runs")

@app.command()  
def schedule_info():
    """Provide guidance on scheduling enrichment runs."""
    print("📅 ENRICHMENT SCHEDULING GUIDE")
    print("=" * 50)
    print()
    print("🔄 RECOMMENDED SCHEDULE:")
    print()
    print("1️⃣  DAILY / WEEKLY:")
    print("   python scripts/run_enrichment_pipeline.py delta-enrich --auto-geometric")
    print("   → The most efficient method. Automatically finds and processes only parcels")
    print("   → with genuine changes, ensuring your data is always current.")
    print()
    print("2️⃣  MONTHLY (or as needed for a broader refresh):")
    print("   python scripts/run_enrichment_pipeline.py incremental-enrich --days-old 30")
    print("   → Catches any parcels that might have been missed by delta detection.")
    print()
    print("3️⃣  QUARTERLY (for data integrity checks):")
    print("   python scripts/run_enrichment_pipeline.py full-refresh")
    print("   → Complete refresh to guarantee data completeness.")
    print()
    print("💡 TIPS:")
    print("   • Monitor with: python scripts/run_monitoring.py status")
    print("   • Get recommendations: python scripts/run_monitoring.py recommend")

if __name__ == "__main__":
    app() 