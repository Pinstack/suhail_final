# Tech Spec: Epic 1 — Performance Index Rollout & Monitoring

Author: Mary (Business Analyst)
Date: 2025-10-16
Status: Draft for Architecture Review

---

## 1. Objective & Scope

Improve query performance and operational visibility for the Meshic pipeline by:
- Applying critical indexes (safe, additive) via Alembic.
- Establishing baseline → post-change performance measurements.
- Providing monitoring outputs for tile queue health and enrichment coverage.
- Automating stale tile resets.

Out of scope: Full observability stack (Prometheus/Grafana). This phase focuses on CLI-based metrics and logs.

---

## 2. Context & Dependencies

- Brownfield state validated at production scale; missing FK/composite indexes cause slow joins on large tables (2.16M+ parcels; 76M+ metrics).
- Alembic migration exists: `19c587b33197_add_critical_performance_indexes.py` adding required indexes + cleaning stray temp tables.
- Built-in utilities:
  - Tile queue model with `claim_tiles_for_processing(...)` and `reset_stale_in_progress(...)`.
  - CLI `monitor` subcommands surface basic monitoring endpoints.

---

## 3. Design

### 3.1 Index Rollout (Alembic)

- Confirm and (re)apply the following indexes in the migration if missing:
  - parcels: `neighborhood_id`, `province_id`, `ruleid`, partial on `transaction_price > 0`, `enriched_at`, composite `(province_id, enriched_at)`
  - parcel_price_metrics: `neighborhood_id`, composite `(metrics_type, year, month)` and `(neighborhood_id, metrics_type)`
  - transactions: `transaction_date`, `transaction_price`
- Ensure temp table cleanup for production hygiene (`temp_*` tables) where safely possible.

### 3.2 Measurement Plan

- For each critical query, capture baseline and post-index timings (p50/p95):
  1) `parcels ↔ neighborhoods` join by `neighborhood_id`
  2) `parcels` filtered by `transaction_price > 0` and `enriched_at`
  3) Time-series reads on `parcel_price_metrics` by `(neighborhood_id, metrics_type, year, month)`
- Store results in `docs/reports/perf-baseline-<date>.md` and `perf-post-<date>.md`.

### 3.3 Monitoring Outputs (CLI)

- `meshic-pipeline monitor status` should include:
  - Tile queue summary: counts by `status`, number of failed, oldest `in_progress` age
  - Enrichment coverage: total parcels, parcels with `enriched_at`, % with `transaction_price > 0`
- `meshic-pipeline monitor recommend`:
  - Next best action (fast-enrich / incremental / delta) with recommended batch sizes
- `meshic-pipeline monitor schedule-info`:
  - Suggested cadence (daily/weekly/monthly) based on current freshness

### 3.4 Stale Reset Automation

- Schedule a periodic task (e.g., cron or systemd timer) invoking `TileURL.reset_stale_in_progress(..., stale_minutes=60)`
- Log count of tiles reset and time taken; ensure idempotency.

---

## 4. Risks & Mitigations

- Risk: Index build time on large tables
  - Mitigation: Use `IF NOT EXISTS`; build off-hours or with reduced traffic; monitor lock duration.
- Risk: Unexpected query plan regressions
  - Mitigation: Collect baseline plans; verify post-change plans with `EXPLAIN ANALYZE`.
- Risk: Monitoring scope creep
  - Mitigation: Limit to CLI text outputs and logs in this epic; push dashboards to later epics.

---

## 5. Acceptance Criteria (from AC doc)

- All specified indexes exist in production; Alembic migration completes without downtime.
- Sample query timings captured (baseline vs post-index) at `docs/reports/perf-baseline-*.md` and `docs/reports/perf-post-index-*.md`.
- Monitoring outputs present and informative; stale reset job operational (`meshic-pipeline monitor reset-stale -- --stale-minutes 60`).
- Investigate any regressions (e.g., broad metrics aggregation still performs full table scan—documented for follow-up tuning).

---

## 6. Implementation Plan

- Step 1: Validate and rerun Alembic migration in staging → production.
- Step 2: Capture baseline query timings; store in docs.
- Step 3: Ensure monitoring commands output required fields; adjust text/logs as needed.
- Step 4: Configure scheduled stale-reset task; document procedure.
- Step 5: Capture post-change timings; update docs; close epic.

---

## 7. Rollback Plan

- Alembic downgrade available for index drops (not recommended in production).
- Revert monitoring changes (CLI) by pinning prior version.
- Disable scheduled stale-reset without impacting pipeline correctness.

---

## 8. References

- docs/BROWNFIELD_PROJECT_DOCUMENTATION.md
- alembic/versions/19c587b33197_add_critical_performance_indexes.py
- src/meshic_pipeline/persistence/models.py (TileURL methods)
- docs/PRD.md, docs/ACCEPTANCE_CRITERIA.md
