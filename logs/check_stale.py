from sqlalchemy import create_engine, text
from meshic_pipeline.config import settings

eng = create_engine(str(settings.database_url))
with eng.connect() as c:
    stale = c.execute(text("SELECT count(*) FROM tile_urls WHERE status='in_progress' AND last_checked_at < now() - interval '5 minutes'")).scalar()
    recent = c.execute(text("SELECT count(*) FROM tile_urls WHERE status='in_progress' AND last_checked_at > now() - interval '1 minute'")).scalar()
    oldest_mins = c.execute(text("SELECT extract(epoch from now() - min(last_checked_at))/60 FROM tile_urls WHERE status='in_progress'")).scalar()
    
print(f"Stale in_progress tiles (>5min): {stale}")
print(f"Recent in_progress tiles (<1min): {recent}")
print(f"Oldest in_progress: {oldest_mins:.1f} minutes ago" if oldest_mins else "None")

# Reset stale tiles
if stale > 0:
    print(f"Resetting {stale} stale tiles...")
    c.execute(text("UPDATE tile_urls SET status='failed', error_message='Stale in_progress reset' WHERE status='in_progress' AND last_checked_at < now() - interval '5 minutes'"))
    c.commit()
    print("Reset complete.")
