# Runbook: critical performance indexes (Epic 1 / STORY-001)

## Scope

Alembic revision **`19c587b33197`** (`alembic/versions/19c587b33197_add_critical_performance_indexes.py`) creates the indexes aligned with **`docs/ACCEPTANCE_CRITERIA.md`** (Epic 1) and **`docs/stories/STORY-001-indexes-migration-validation.md`**.

Rationale and historical analysis: **`docs/archive/legacy-root-md/DATABASE_ARCHITECTURE_ANALYSIS.md`**.

## Preconditions

- `DATABASE_URL` set (see **`.env.example`**).
- Postgres + PostGIS; backup / low-traffic window per your SOP.
- Optional: baseline timings before apply (see reports below).

## Apply

```bash
# From repo root
uv run alembic upgrade head
# or: uv run python scripts/db/upgrade.py
```

## Verify

1. **Indexes present** — compare to migration and AC (e.g. `pg_indexes` / `\d+` on `parcels`, `parcel_price_metrics`, `transactions`).
2. **Plans** — `EXPLAIN (ANALYZE, BUFFERS)` on the three representative queries documented in **`docs/tech-specs/EPIC-001-performance-and-monitoring.md`**.
3. **Side effects** — migration may `ALTER` `building_rules.zoning_id` to `BIGINT` and `DROP` listed `temp_*` tables; confirm in non-prod first.

## Evidence / performance reports (committed)

| Artifact | Path |
|----------|------|
| Baseline (2025-10-17) | [../reports/perf-baseline-20251017-1152.md](../reports/perf-baseline-20251017-1152.md) |
| Post-index (2025-10-17) | [../reports/perf-post-index-20251017-1154.md](../reports/perf-post-index-20251017-1154.md) |

**Note:** Those samples show **p95 above 500 ms** for the documented queries. Treat Epic 1 latency targets as **aspirational** until re-measured on production-like data volume and hardware; update this runbook when new timings are captured.

## After apply

- Add a dated row or appendix here (or new `docs/reports/perf-post-index-YYYYMMDD-HHMM.md`) with: environment, row counts, `EXPLAIN` summary, p50/p95.
- Update **`docs/stories/STORY-001-indexes-migration-validation.md`** status when DoD is met.
