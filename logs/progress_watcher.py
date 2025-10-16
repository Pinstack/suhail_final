import sys, time
from sqlalchemy import create_engine, text
from meshic_pipeline.config import settings

def snapshot():
    e = create_engine(str(settings.database_url))
    with e.connect() as c:
        total = c.execute(text("select count(*) from tile_urls")).scalar()
        rows = dict(c.execute(text("select status, count(*) from tile_urls group by status")).all())
        parcels = c.execute(text("select count(*) from parcels")).scalar()
    processed = rows.get("processed", 0)
    pending = rows.get("pending", 0)
    inprog = rows.get("in_progress", 0)
    failed = rows.get("failed", 0) + rows.get("permanent_failed", 0)
    pct = (processed / max(total, 1)) * 100.0
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] Parcels: {parcels:,} | Tiles: {processed}/{total} ({pct:.1f}%) | {rows} | Failed: {failed}")
    sys.stdout.flush()
    return pending, inprog

def main():
    while True:
        try:
            pending, inprog = snapshot()
            if pending == 0 and inprog == 0:
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                print(f"[{ts}] DONE")
                sys.stdout.flush()
                break
        except Exception as e:
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{ts}] ERROR: {e}")
            sys.stdout.flush()
        time.sleep(60)

if __name__ == "__main__":
    main()
