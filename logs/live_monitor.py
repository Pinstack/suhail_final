#!/usr/bin/env python3
"""
Live terminal monitor for the countrywide scraping pipeline.
Shows real-time progress with tqdm, rates, and adaptive concurrency status.
"""

import sys
import time
from datetime import datetime, timedelta
from tqdm import tqdm
from sqlalchemy import create_engine, text
from meshic_pipeline.config import settings

class PipelineMonitor:
    def __init__(self):
        self.engine = create_engine(str(settings.database_url))
        self.start_time = datetime.now()
        self.last_processed = 0
        self.last_check_time = datetime.now()
        
    def get_status(self):
        """Get current pipeline status from database."""
        with self.engine.connect() as c:
            total = c.execute(text("select count(*) from tile_urls")).scalar()
            status_counts = dict(c.execute(text("select status, count(*) from tile_urls group by status")).all())
            parcels = c.execute(text("select count(*) from parcels")).scalar()
            
            # Recent activity check
            recent_parcels = c.execute(text("select count(*) from parcels where updated_at > now() - interval '5 minutes'")).scalar()
            
        return {
            'total': total,
            'processed': status_counts.get('processed', 0),
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'failed': status_counts.get('failed', 0) + status_counts.get('permanent_failed', 0),
            'parcels': parcels,
            'recent_activity': recent_parcels > 0,
            'status_counts': status_counts
        }
    
    def calculate_rate(self, current_processed):
        """Calculate tiles per second processing rate."""
        now = datetime.now()
        time_diff = (now - self.last_check_time).total_seconds()
        if time_diff > 0 and self.last_processed > 0:
            tiles_diff = current_processed - self.last_processed
            rate = tiles_diff / time_diff
        else:
            rate = 0
        
        self.last_processed = current_processed
        self.last_check_time = now
        return rate
    
    def calculate_eta(self, processed, total, rate):
        """Calculate estimated time to completion."""
        if rate > 0 and processed < total:
            remaining = total - processed
            eta_seconds = remaining / rate
            return timedelta(seconds=int(eta_seconds))
        return None
    
    def format_duration(self, td):
        """Format timedelta for display."""
        if td is None:
            return "unknown"
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def run(self, refresh_interval=5):
        """Run the live monitor with tqdm progress bar."""
        print("🚀 Starting live pipeline monitor...")
        print("Press Ctrl+C to exit")
        
        # Initial status to set up progress bar
        status = self.get_status()
        total = status['total']
        
        with tqdm(
            total=total,
            unit=' tiles',
            desc='Pipeline Progress',
            bar_format='{desc}: {percentage:3.1f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as pbar:
            
            try:
                while True:
                    status = self.get_status()
                    processed = status['processed']
                    rate = self.calculate_rate(processed)
                    eta = self.calculate_eta(processed, total, rate)
                    
                    # Update progress bar
                    pbar.n = processed
                    pbar.refresh()
                    
                    # Create detailed status line
                    elapsed = datetime.now() - self.start_time
                    status_line = (
                        f"📊 Parcels: {status['parcels']:,} | "
                        f"Queue: P:{status['pending']} IP:{status['in_progress']} F:{status['failed']} | "
                        f"Rate: {rate:.1f} tiles/s | "
                        f"ETA: {self.format_duration(eta)} | "
                        f"Elapsed: {self.format_duration(elapsed)}"
                    )
                    
                    if not status['recent_activity']:
                        status_line += " ⚠️  No recent activity"
                    
                    # Clear previous line and print new status
                    print(f"\r{' ' * 120}\r{status_line}", end='', flush=True)
                    
                    # Check if done
                    if status['pending'] == 0 and status['in_progress'] == 0:
                        print(f"\n\n🎉 Pipeline completed!")
                        print(f"📊 Final stats: {status['parcels']:,} parcels from {processed:,} tiles")
                        print(f"⏱️  Total time: {self.format_duration(elapsed)}")
                        break
                    
                    time.sleep(refresh_interval)
                    
            except KeyboardInterrupt:
                print(f"\n\n👋 Monitor stopped by user")
                print(f"📊 Current progress: {processed:,}/{total:,} tiles ({(processed/total)*100:.1f}%)")
                print(f"📦 Parcels captured: {status['parcels']:,}")

def main():
    monitor = PipelineMonitor()
    monitor.run(refresh_interval=3)  # Update every 3 seconds

if __name__ == '__main__':
    main()
