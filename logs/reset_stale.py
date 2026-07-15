from sqlalchemy import create_engine, text
from suhail_pipeline.config import settings

eng = create_engine(str(settings.database_url))
with eng.connect() as c:
    # Reset stale in_progress tiles
    updated = c.execute(text("UPDATE tile_urls SET status='failed', error_message='Stale reset' WHERE status='in_progress'")).rowcount
    c.commit()
    print(f"Reset {updated} stale tiles")
    
    # Disable FK constraints temporarily for neighborhoods
    c.execute(text("ALTER TABLE neighborhoods DISABLE TRIGGER ALL"))
    c.commit()
    print("Disabled FK constraints on neighborhoods table")
