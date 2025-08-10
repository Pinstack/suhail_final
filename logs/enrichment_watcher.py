#!/usr/bin/env python3
"""
Enrichment completion watcher - monitors the pipeline and notifies when done
"""
import time
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.meshic_pipeline.config import settings
from sqlalchemy import create_engine

def check_process_running(pid_file):
    """Check if process is still running"""
    try:
        with open(pid_file, 'r') as f:
            pid = int(f.read().strip())
        
        # Check if process exists
        result = subprocess.run(['ps', '-p', str(pid)], 
                              capture_output=True, text=True)
        return result.returncode == 0
    except (FileNotFoundError, ValueError):
        return False

def get_enrichment_status():
    """Get current enrichment status"""
    from sqlalchemy import text
    engine = create_engine(str(settings.database_url))
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total,
                COUNT(enriched_at) as enriched,
                COUNT(*) - COUNT(enriched_at) as remaining
            FROM parcels
        """)).fetchone()
        return result

def notify_completion(total_enriched):
    """Print completion notification"""
    print("\n" + "="*60)
    print("🎉 ENRICHMENT PIPELINE COMPLETED! 🎉")
    print("="*60)
    print(f"✅ Successfully enriched {total_enriched:,} parcels")
    print(f"📅 Completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Database ready for analysis and export")
    print("="*60)
    
    # Also write to a completion file
    with open('logs/enrichment_complete.txt', 'w') as f:
        f.write(f"ENRICHMENT COMPLETED\n")
        f.write(f"Completion time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total parcels enriched: {total_enriched:,}\n")

def main():
    pid_file = 'logs/enrichment-full.pid'
    print("👀 Watching enrichment pipeline for completion...")
    print("🔄 Checking every 5 minutes")
    print("⏹️  Press Ctrl+C to stop watching\n")
    
    last_status_time = 0
    
    while True:
        try:
            # Check if process is still running
            process_running = check_process_running(pid_file)
            
            # Get current status
            total, enriched, remaining = get_enrichment_status()
            
            # Print status update every 15 minutes
            current_time = time.time()
            if current_time - last_status_time > 900:  # 15 minutes
                timestamp = time.strftime("%H:%M:%S")
                progress = (enriched / total) * 100
                print(f"[{timestamp}] Progress: {enriched:,}/{total:,} ({progress:.1f}%) - "
                      f"Process: {'Running' if process_running else 'Stopped'}")
                last_status_time = current_time
            
            # Check for completion
            if remaining == 0:
                notify_completion(enriched)
                break
            
            # Check if process died unexpectedly
            if not process_running and remaining > 0:
                print(f"\n⚠️  WARNING: Process stopped but {remaining:,} parcels remain!")
                print(f"📝 Check logs/enrichment-full.log for errors")
                print(f"🔄 You may need to restart: meshic-pipeline full-refresh")
                break
                
        except KeyboardInterrupt:
            print(f"\n👋 Stopped watching by user request")
            break
        except Exception as e:
            print(f"\n❌ Error monitoring: {e}")
            time.sleep(60)
            continue
            
        time.sleep(300)  # Check every 5 minutes

if __name__ == "__main__":
    main()
