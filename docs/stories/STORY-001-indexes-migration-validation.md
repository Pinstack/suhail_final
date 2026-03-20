# Story 001: Validate and Apply Critical Indexes

Epic: Performance Index Rollout & Query Tuning
Type: Technical
Owner: Data Engineering
Status: Ready for Dev

## Goal
Ensure all required indexes exist in production to improve query performance on 2M+ parcels and 76M+ metrics.

## Tasks
- Verify Alembic migration `19c587b33197_add_critical_performance_indexes.py` in staging.
- Run migration in production during low-traffic window.
- Confirm index presence via `pg_indexes` and `EXPLAIN` plans.
- Record before/after timings and attach to `docs/reports/perf-post-<date>.md`.

## Acceptance Criteria
- All specified indexes exist (see docs/ACCEPTANCE_CRITERIA.md).
- p95 latency < 500 ms for common queries under representative load.
- Migration completes without downtime or errors.

## Definition of Done
- Reports committed to repo; runbook updated.

## References
- Runbook: [../ops/index-migration-runbook.md](../ops/index-migration-runbook.md)
- Existing perf captures: [../reports/perf-baseline-20251017-1152.md](../reports/perf-baseline-20251017-1152.md), [../reports/perf-post-index-20251017-1154.md](../reports/perf-post-index-20251017-1154.md)
