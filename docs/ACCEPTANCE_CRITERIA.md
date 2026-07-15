# Acceptance Criteria: Suhail Geospatial Data Pipeline

Date: 2025-10-16
Author: Mary (Business Analyst)

---

## Epic 1: Performance Index Rollout & Query Tuning

- Index Presence
  - The following indexes exist in production (verify via `pg_indexes`):
    - `parcels(neighborhood_id)`, `parcels(province_id)`, `parcels(ruleid)`
    - `parcel_price_metrics(neighborhood_id)`
    - Partial: `parcels(transaction_price) WHERE transaction_price > 0`
    - `parcels(enriched_at)`
    - Composite: `parcels(province_id, enriched_at)`
    - `transactions(transaction_date)`, `transactions(transaction_price)`
    - `parcel_price_metrics(metrics_type, year, month)` and `(neighborhood_id, metrics_type)`
- Measured Performance
  - p95 latency for common queries < 500ms under representative load:
    - Join `parcels ↔ neighborhoods` by `neighborhood_id`
    - Filter `parcels` by `transaction_price > 0` and `enriched_at`
    - Time-series reads from `parcel_price_metrics` by `(neighborhood_id, metrics_type, year, month)`
- Zero Downtime
  - Index creation applied via Alembic without downtime; no failed migrations.
- Observability
  - Baseline and post-migration query timings recorded and linked in runbook.

## Epic 2: Monitoring & Alerting

- Monitoring CLI
  - `suhail-pipeline monitor status` outputs tile queue counts by status, top errors, and age of oldest `in_progress`.
  - `suhail-pipeline monitor recommend` outputs actionable scheduling guidance (which enrichment strategy to run next, with batch sizes).
  - `suhail-pipeline monitor schedule-info` displays recommended cadence (daily/weekly/monthly) based on data freshness.
- Stale Reset
  - Scheduled job resets stale `in_progress` tiles after configurable threshold (e.g., 60 minutes) using built-in method.
  - Reset operations are logged with count of tiles affected.
- Metrics Export
  - Tiles/hour and enrichment counts per run are emitted to logs; optionally exported to a simple CSV or dashboard location.

## Epic 3: Delta Enrichment Productization

- Fresh Table Lifecycle
  - Fresh MVT table name is configurable (default `parcels_fresh_mvt`).
  - Table is created when `--auto-geometric` is used and dropped after successful run.
- Change Stats
  - Run summary reports change categories and counts (new parcel w/ transaction, null→positive, zero→positive, price changed, price disappeared).
  - Summary printed and logged; return code indicates success/failure.
- Scheduling
  - Documented schedule (weekly/monthly) for delta runs; compatible with monitoring recommendations.

## Epic 4: Data Quality Framework

- Completeness
  - Coverage report shows % of parcels with `neighborhood_id`, `province_id`, and `enriched_at`.
- Validity
  - Outlier detection thresholds for `price_of_meter` and `transaction_price` are defined and reported.
- Reporting
  - Data quality report generated to `docs/reports/data-quality-<date>.md` with key metrics.

## Epic 5: API/Productization

- Access Layer
  - API design documented (REST or GraphQL) with authentication and rate limits.
  - At least one endpoint returns parcel intelligence by `parcel_objectid` and by `neighborhood_id`.
- Performance
  - p95 API response times meet targets (< 500 ms for typical reads on indexed fields).
- Stability
  - Error handling and pagination documented; sample requests included.

## Epic 6: Schema Hygiene & Normalization

- Type Consistency
  - `building_rules.max_building_coefficient` and `max_building_height` migrated to DECIMAL.
  - `building_rules.zoning_id` type aligned with `parcels.zoning_id` (BIGINT).
- Normalization Plan
  - Proposal documented to reduce redundancy in price metrics and standardize foreign key usage.
- Safe Migrations
  - Alembic migrations created, tested in staging, and applied to production without data loss.

## Epic 7: Documentation Transition

- Source of Truth
  - BMAD docs (Brief, PRD, Acceptance Criteria, Tech Spec) are the authoritative documentation.
  - README reflects production scale and correct CLI commands.
- Retirement
  - Memory-bank references are labeled historical; any conflicting numbers removed or reconciled.

