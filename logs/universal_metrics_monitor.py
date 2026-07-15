#!/usr/bin/env python3
"""
Universal metrics enrichment monitor - tracks progress and provides live updates
"""
import time
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.suhail_pipeline.config import settings
from sqlalchemy import create_engine, text
from tqdm import tqdm

def check_process_running(pid_file):
    """Check if process is still running"""
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        result = subprocess.run(['ps', '-p', str(pid)], 
                              capture_output=True, text=True)
        return result.returncode == 0, pid
    except (FileNotFoundError, ValueError):
        return False, None

def get_metrics_status():
    """Get current metrics enrichment status"""
    engine = create_engine(str(settings.database_url))
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_parcels,
                COUNT(CASE WHEN parcel_objectid IN (
                    SELECT DISTINCT parcel_objectid FROM parcel_price_metrics
                ) THEN 1 END) as parcels_with_metrics,
                (SELECT COUNT(*) FROM parcel_price_metrics) as total_metrics
            FROM parcels
        """)).fetchone()
        return result

def main():
    pid_file = 'logs/universal-metrics.pid'
    print("🎯 Universal Metrics Enrichment Monitor")
    print("="*50)
    print("📊 Processing all 2.3M parcels for derived price metrics")
    print("⏰ Checking every 30 seconds")
    print("🔄 Press Ctrl+C to stop monitoring\n")
    
    start_time = time.time()
    last_metrics_count = 0
    
    # Get initial status
    total_parcels, initial_enriched, initial_metrics = get_metrics_status()
    
    with tqdm(total=total_parcels, unit="parcel", dynamic_ncols=True, position=0, leave=True) as pbar:
        pbar.n = initial_enriched
        pbar.set_description("🎯 Universal Metrics")
        pbar.refresh()
        
        while True:
            try:
                # Check if process is running
                process_running, pid = check_process_running(pid_file)
                
                # Get current status
                total_parcels, current_enriched, current_metrics = get_metrics_status()
                
                # Update progress bar
                pbar.total = total_parcels
                pbar.n = current_enriched
                
                # Calculate rates
                elapsed_time = time.time() - start_time
                parcels_rate = (current_enriched - initial_enriched) / max(elapsed_time, 1)
                metrics_rate = (current_metrics - last_metrics_count) / 30 if last_metrics_count > 0 else 0
                last_metrics_count = current_metrics
                
                # Calculate ETA
                remaining_parcels = total_parcels - current_enriched
                if parcels_rate > 0:
                    eta_seconds = remaining_parcels / parcels_rate
                    eta_str = time.strftime("%Hh %Mm", time.gmtime(eta_seconds))
                else:
                    eta_str = "calculating..."
                
                # Update display
                status_emoji = "🟢" if process_running else "🔴"
                pbar.set_description(
                    f"{status_emoji} Metrics: {current_enriched:,}/{total_parcels:,} "
                    f"({current_enriched/total_parcels*100:.1f}%) | "
                    f"📈 {current_metrics:,} total metrics | "
                    f"⚡ {parcels_rate:.1f} parcels/s | "
                    f"🕐 ETA: {eta_str}"
                )
                pbar.refresh()
                
                # Check for completion
                if not process_running and remaining_parcels == 0:
                    print(f"\n🎉 UNIVERSAL METRICS COMPLETED!")
                    print(f"✅ All {total_parcels:,} parcels processed")
                    print(f"📊 Total metrics captured: {current_metrics:,}")
                    break
                elif not process_running and remaining_parcels > 0:
                    print(f"\n⚠️  Process stopped with {remaining_parcels:,} parcels remaining")
                    print(f"📝 Check logs/universal-metrics-full.log for details")
                    break
                    
            except KeyboardInterrupt:
                print(f"\n👋 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                
            time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    main()
