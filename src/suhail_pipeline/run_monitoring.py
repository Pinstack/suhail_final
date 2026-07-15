#!/usr/bin/env python3
"""
Monitoring utilities for Suhail pipeline.
Provides:
- status: queue + enrichment overview
- recommend: next action suggestions
- schedule-info: cadence guidance
- reset-stale: reset stale in_progress tiles
"""

import typer
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from pathlib import Path
import time
import statistics

from suhail_pipeline.config import settings

app = typer.Typer()

@app.command()
def status():
    """Show queue status, enrichment coverage, and freshness."""
    engine = create_engine(str(settings.database_url))

    with engine.connect() as conn:
        # Queue counts
        queue = conn.execute(text(
            """
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE status = 'pending') AS pending,
              COUNT(*) FILTER (WHERE status = 'in_progress') AS in_progress,
              COUNT(*) FILTER (WHERE status = 'processed') AS processed,
              COUNT(*) FILTER (WHERE status = 'failed') AS failed
            FROM public.tile_urls
            """
        )).mappings().first() or {}

        # Oldest in_progress age and top errors
        oldest = conn.execute(text(
            """
            SELECT MIN(last_checked_at)
            FROM public.tile_urls
            WHERE status = 'in_progress' AND last_checked_at IS NOT NULL
            """
        )).scalar()
        top_errors = conn.execute(text(
            """
            SELECT COALESCE(error_message,'<none>') AS error, COUNT(*) AS cnt
            FROM public.tile_urls
            WHERE status = 'failed'
            GROUP BY error
            ORDER BY cnt DESC
            LIMIT 5
            """
        )).fetchall()

        # Enrichment counts
        total_parcels = conn.execute(text("SELECT COUNT(*) FROM public.parcels WHERE transaction_price > 0")).scalar() or 0
        enriched_parcels = conn.execute(text("SELECT COUNT(*) FROM public.parcels WHERE enriched_at IS NOT NULL")).scalar() or 0
        tx_count = conn.execute(text("SELECT COUNT(*) FROM public.transactions")).scalar() or 0

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

        print("📊 PIPELINE STATUS REPORT")
        print("=" * 60)
        print("🧱 Tile Queue:")
        if queue:
            print(f"   • Total:     {queue.get('total',0):,}")
            print(f"   • Pending:   {queue.get('pending',0):,}")
            print(f"   • In-Progress: {queue.get('in_progress',0):,}")
            print(f"   • Processed: {queue.get('processed',0):,}")
            print(f"   • Failed:    {queue.get('failed',0):,}")
        else:
            print("   • No tile_urls table or no records found")
        if oldest:
            age_min = max(0, int((datetime.utcnow() - oldest.replace(tzinfo=None)).total_seconds() // 60))
            print(f"   • Oldest in_progress age: {age_min} minutes")
        if top_errors:
            print("   • Top errors (failed):")
            for err, cnt in top_errors:
                print(f"      - {cnt:>6} × {err}")
        print()

        print(f"📊 Parcel Overview:")
        print(f"   • Total enrichable parcels: {total_parcels:,}")
        print(f"   • Enriched parcels:         {enriched_parcels:,}")
        unenriched = max(total_parcels - enriched_parcels, 0)
        coverage = (enriched_parcels/total_parcels)*100 if total_parcels else 0.0
        print(f"   • Unenriched parcels:       {unenriched:,}")
        print(f"   • Coverage:                 {coverage:.1f}%")
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
    """Recommend next enrichment strategy and commands."""
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
            print(f"🚀 HIGHEST PRIORITY: {new_parcels:,} unenriched parcels with transaction data")
            print(f"   💡 Stage 1 revealed parcels with transaction_price > 0.")
            print(f"   Recommended: suhail-pipeline fast-enrich --batch-size 400")
            print("   → Leverages transaction_price field from MVT tiles for maximum efficiency")
            print()
        elif new_parcels > 1000:
            print(f"🆕 HIGH PRIORITY: {new_parcels:,} unenriched parcels found")
            print(f"   Recommended: suhail-pipeline fast-enrich --batch-size 300")
            print()
        
        # Priority 2: Incremental updates for already enriched parcels
        if stale_7d > 5000:
            print(f"⚠️  MEDIUM PRIORITY: {stale_7d:,} stale parcels (7+ days)")
            print(f"   💡 May have new transactions not yet captured")
            print(f"   Recommended: suhail-pipeline incremental-enrich --days-old 7")
            print()
        elif stale_30d > 1000:
            print(f"⏰ LOW PRIORITY: {stale_30d:,} stale parcels (30+ days)") 
            print(f"   Recommended: suhail-pipeline incremental-enrich --days-old 30")
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
        print("      suhail-pipeline delta-enrich --auto-geometric")
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
    print("   suhail-pipeline delta-enrich --auto-geometric")
    print("   → The most efficient method. Automatically finds and processes only parcels")
    print("   → with genuine changes, ensuring your data is always current.")
    print()
    print("2️⃣  MONTHLY (or as needed for a broader refresh):")
    print("   suhail-pipeline incremental-enrich --days-old 30")
    print("   → Catches any parcels that might have been missed by delta detection.")
    print()
    print("3️⃣  QUARTERLY (for data integrity checks):")
    print("   suhail-pipeline full-refresh")
    print("   → Complete refresh to guarantee data completeness.")
    print()
    print("💡 TIPS:")
    print("   • Monitor with: suhail-pipeline monitor status")
    print("   • Get recommendations: suhail-pipeline monitor recommend")

@app.command(name="reset-stale")
def reset_stale(stale_minutes: int = typer.Option(60, "--stale-minutes", help="Minutes after which in_progress tiles are considered stale")):
    """Reset stale in_progress tiles to failed so they can be retried."""
    from sqlalchemy.orm import Session
    from suhail_pipeline.persistence.db import get_db_engine
    from suhail_pipeline.persistence.models import TileURL

    engine = get_db_engine(str(settings.database_url))
    session = Session(engine)
    updated = TileURL.reset_stale_in_progress(session, stale_minutes=stale_minutes)
    print(f"🔄 Reset {updated} stale in_progress tiles (threshold: {stale_minutes} minutes)")
    session.close()

@app.command(name="perf")
def perf(
    label: str = typer.Option("baseline", "--label", help="Label for this measurement run (e.g., baseline, post-index)"),
    iterations: int = typer.Option(5, "--iterations", help="How many times to run each query"),
    write_report: bool = typer.Option(True, "--write-report/--no-report", help="Write Markdown report to docs/reports"),
):
    """Measure sample query performance and optionally write a Markdown report."""
    engine = create_engine(str(settings.database_url))
    queries = [
        (
            "Parcels join neighborhoods (priced)",
            """
            SELECT COUNT(*)
            FROM public.parcels p
            JOIN public.neighborhoods n ON p.neighborhood_id = n.neighborhood_id
            WHERE p.transaction_price > 0
            """,
        ),
        (
            "Stale enrichable parcels",
            """
            SELECT COUNT(*)
            FROM public.parcels
            WHERE transaction_price > 0
              AND (enriched_at IS NULL OR enriched_at < NOW() - INTERVAL '30 days')
            """,
        ),
        (
            "Metrics aggregation (recent avg price)",
            """
            SELECT neighborhood_id, metrics_type, year, month, AVG(average_price_of_meter)
            FROM public.parcel_price_metrics
            WHERE metrics_type = 'average_price_of_meter'
              AND year >= EXTRACT(YEAR FROM CURRENT_DATE) - 1
            GROUP BY neighborhood_id, metrics_type, year, month
            LIMIT 10000
            """,
        ),
    ]

    results = []
    with engine.connect() as conn:
        for name, sql in queries:
            durations = []
            # Warm-up run (not timed)
            try:
                conn.execute(text("SELECT 1")).scalar()
            except Exception:
                pass
            for _ in range(max(iterations, 1)):
                start = time.perf_counter()
                conn.execute(text(sql)).fetchall()
                end = time.perf_counter()
                durations.append((end - start) * 1000.0)  # ms
            durations.sort()
            p50 = statistics.median(durations)
            p95 = durations[int(len(durations) * 0.95) - 1] if durations else 0.0
            results.append((name, durations, p50, p95))

    # Print summary
    print("📌 Performance Sample Results —", label)
    print("=" * 60)
    for name, durations, p50, p95 in results:
        avg = sum(durations) / len(durations)
        print(f"• {name}")
        print(f"  - iters={len(durations)} avg={avg:.1f}ms p50={p50:.1f}ms p95={p95:.1f}ms")

    if write_report:
        ts = datetime.utcnow().strftime("%Y%m%d-%H%M")
        out_dir = Path(__file__).resolve().parents[2] / "docs" / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"perf-{label}-{ts}.md"
        lines = [
            f"# Performance Sample Results — {label}",
            "",
            f"Date (UTC): {datetime.utcnow().isoformat()}",
            "",
        ]
        for name, durations, p50, p95 in results:
            avg = sum(durations) / len(durations)
            lines += [
                f"## {name}",
                f"- iterations: {len(durations)}",
                f"- average: {avg:.1f} ms",
                f"- p50: {p50:.1f} ms",
                f"- p95: {p95:.1f} ms",
                "",
            ]
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"📝 Wrote report: {out_path}")

if __name__ == "__main__":
    app() 
