# Operations: Database Migrations

This project uses Alembic for schema and performance index management.

## Prerequisites
- DATABASE_URL set in `.env` or environment.
- Postgres with PostGIS installed.

## Upgrade to latest
```bash
python scripts/db/upgrade.py            # upgrades to head
# or interactively
alembic upgrade head
```

## Downgrade (use with caution)
```bash
python scripts/db/downgrade.py -1       # one revision down
python scripts/db/downgrade.py base     # back to initial
```

## Notes
- Critical performance indexes are applied by `19c587b33197_add_critical_performance_indexes.py`.
- This migration also cleans up stray `temp_*` tables where safe.
- Apply during low-traffic windows; collect baseline and post timings (see monitoring perf command).
- If provinces metadata is incomplete (missing tile URL/bbox), repair it with
  `python scripts/util/backfill_province_metadata.py --province-id <id>` before running
  auto-geometric delta pipelines.
