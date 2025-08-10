#!/usr/bin/env python3
"""Monitor enrichment pipeline progress"""
import time
import sys
from sqlalchemy import create_engine
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.meshic_pipeline.config import settings

def monitor_enrichment():
    engine = create_engine(str(settings.database_url))
    
    print("🔍 Enrichment Pipeline Monitor")
    print("=" * 50)
    print("Press Ctrl+C to exit")
    print()
    
    start_time = time.time()
    last_enriched_count = 0
    
    while True:
        try:
            with engine.connect() as conn:
                # Get enrichment status
                result = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(enriched_at) as enriched,
                        COUNT(*) - COUNT(enriched_at) as remaining
                    FROM parcels
                """).fetchone()
                
                total, enriched, remaining = result
                
                # Calculate progress
                progress_pct = (enriched / total) * 100
                
                # Calculate rate
                elapsed = time.time() - start_time
                if elapsed > 0:
                    rate = (enriched - last_enriched_count) / elapsed if elapsed > 60 else 0
                    if rate > 0:
                        eta_seconds = remaining / rate
                        eta_str = time.strftime("%Hh %Mm", time.gmtime(eta_seconds))
                    else:
                        eta_str = "calculating..."
                else:
                    rate = 0
                    eta_str = "calculating..."
                
                # Display status
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"\r[{timestamp}] Enriched: {enriched:,}/{total:,} ({progress_pct:.2f}%) | "
                      f"Rate: {rate:.1f}/min | ETA: {eta_str} | Remaining: {remaining:,}", 
                      end="", flush=True)
                
                # Check if complete
                if remaining == 0:
                    print(f"\n🎉 Enrichment Complete! All {total:,} parcels enriched.")
                    break
                
                # Reset counters
                last_enriched_count = enriched
                start_time = time.time()
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Monitor stopped by user")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            break
            
        time.sleep(60)  # Update every minute

if __name__ == "__main__":
    monitor_enrichment()
