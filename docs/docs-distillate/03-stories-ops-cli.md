This section covers implementation stories, CLI inventory, ops, and runbooks. Part 3 of 3.

## Stories and backlog
- STORY-001: Validate/apply critical indexes; Epic: Performance Index Rollout and Query Tuning; Owner: Data Engineering; Status: Ready for Dev.
- STORY-001: Verify Alembic migration `19c587b33197_add_critical_performance_indexes.py` in staging; run in prod low-traffic; confirm via `pg_indexes` and `EXPLAIN`; record timings in `docs/reports/perf-post-<date>.md`.
- STORY-001: Acceptance: indexes per `docs/ACCEPTANCE_CRITERIA.md`; p95 < 500 ms; migration without downtime/errors; DoD: reports + runbook.
- STORY-002: Baseline/post-index p50/p95 for 3 representative queries; `docs/reports/perf-baseline-<date>.md` and `perf-post-<date>.md`; p95 target < 500 ms or remediation plan.
- STORY-003: Enhance `meshic-pipeline monitor`: `status` (queue by status, oldest `in_progress`, top errors); `recommend` (next action + batch sizes); `schedule-info` (cadence); structured log summary per run.
- STORY-004: Schedule `TileURL.reset_stale_in_progress(..., stale_minutes=60)`; log reset count; alert if excessive repeats; runbook + monitoring reflects queue health.
- STORY-005: Delta enrichment: `--auto-geometric` fresh-table lifecycle; change stats/summary; cron guidance; fresh table dropped on success, retained on failure with warning.
- STORY-006: Data quality Phase 1: completeness `%` with `neighborhood_id`, `province_id`, `enriched_at`; outlier thresholds `price_of_meter`, `transaction_price`; `docs/reports/data-quality-<date>.md` by province.
- STORY-007: API design doc (REST/GraphQL) + minimal skeleton; auth/rate limits; stub ≥2 endpoints locally; feature flag or separate service dir.
- STORY-008: Docs transition to BMAD: README scale, correct CLI/monitoring, temp tables note; cross-links Brief/PRD/AC/Tech Spec; memory-bank historical/reconciled.

## Epic / tech spec (EPIC-001 performance and monitoring)
- EPIC-001 scope: Alembic critical indexes; baseline→post measurements; CLI monitoring for tile queue + enrichment coverage; automate stale tile resets; out of scope: full Prometheus/Grafana.
- Scale context: 2.16M+ parcels; 76M+ metrics; brownfield missing FK/composite indexes slowing joins.
- Migration `19c587b33197_add_critical_performance_indexes.py`: indexes + safe cleanup of stray `temp_*` tables.
- Index targets (parcels): `neighborhood_id`, `province_id`, `ruleid`, partial `transaction_price > 0`, `enriched_at`, composite `(province_id, enriched_at)`.
- Index targets (`parcel_price_metrics`): `neighborhood_id`; composites `(metrics_type, year, month)` and `(neighborhood_id, metrics_type)`.
- Index targets (`transactions`): `transaction_date`, `transaction_price`.
- Measurement queries: (1) `parcels ↔ neighborhoods` on `neighborhood_id`; (2) `parcels` filter `transaction_price > 0` and `enriched_at`; (3) time-series `parcel_price_metrics` by `(neighborhood_id, metrics_type, year, month)`.
- `meshic-pipeline monitor status`: queue counts by `status`, failed count, oldest `in_progress` age; enrichment: total parcels, with `enriched_at`, % with `transaction_price > 0`.
- `meshic-pipeline monitor recommend`: next action among fast-enrich / incremental / delta with batch sizes.
- `meshic-pipeline monitor schedule-info`: suggested daily/weekly/monthly cadence from freshness.
- AC mentions: `meshic-pipeline monitor reset-stale -- --stale-minutes 60`; reports `docs/reports/perf-baseline-*.md` and `docs/reports/perf-post-index-*.md` (naming variant vs stories).
- Risks: index build time/locks → `IF NOT EXISTS`, off-hours; plan regressions → `EXPLAIN ANALYZE`; limit CLI scope vs dashboards.
- Utilities referenced: `claim_tiles_for_processing(...)`, `TileURL.reset_stale_in_progress(...)` in `src/meshic_pipeline/persistence/models.py`.

## CLI inventory and documentation gaps (`CLI_COMMAND_AUDIT.md`)
- Commands: `geometric` (`--bbox`, `--recreate-db`, `--save-as-temp`); `fast-enrich` (`--batch-size`, `--limit`); `incremental-enrich` (`--batch-size`, `--days-old`, `--limit`); `full-refresh` (`--batch-size`, `--limit`).
- `delta-enrich`: `--batch-size`, `--limit`, `--fresh-table`, `--auto-geometric`, `--show-details`.
- `smart-pipeline`: `--geometric-first`, `--batch-size`, `--bbox` (DB-driven orchestration standard).
- `monitor`: `status`, `recommend`, `schedule-info`.
- `province-geometric`: `province`, `--strategy`, `--recreate-db`, `--save-as-temp`.
- `saudi-arabia-geometric`: `--strategy`, `--recreate-db`, `--save-as-temp`.
- `discovery-summary`: no options; DB-driven summary.
- `province-pipeline`: `province`, `--strategy`, `--batch-size`, `--geometric-first`.
- `saudi-pipeline`: `--strategy`, `--batch-size`, `--geometric-first`.
- Recommendations: remove legacy tile-discovery CLI refs; document all flags; standardize syntax; improve `--help`; add advanced/composite examples.

## Province-wide scraping (DB-driven MVT)
- Authoritative: `provinces` metadata; `tile_urls` tile list/status; config from DB; no hard-coded province dicts/YAML tile lists.
- Downloader: async; province + tiles from DB; caching, retry, concurrency; resumable multi/all-province.
- CLI examples: `meshic-pipeline geometric --province riyadh`; `meshic-pipeline geometric --all-provinces`; multi `--province riyadh --province makkah`.
- Performance: index `tile_urls` by status/province; spatial/lookup indices on parcels/neighborhoods at >1M/province; ~5000-row chunks (settings-tunable); disk tile cache.
- CI suggestion: nightly `meshic-pipeline geometric --province riyadh --limit-test`.
- Rollout phases: DB metadata+generator → downloader/refactor → orchestrator+CLI `--all-provinces` → tests/CI → docs → full Riyadh → six provinces (success metrics in doc table).
- Risks: rate limit (0.05s delay, backoff); memory (stream, chunk tuning); DB province drift (runtime validation).

## Ops: migrations (`docs/ops/migrations.md`)
- Prereqs: `DATABASE_URL` in `.env`; Postgres + PostGIS.
- Upgrade: `python scripts/db/upgrade.py` or `alembic upgrade head`.
- Downgrade: `python scripts/db/downgrade.py -1` or `python scripts/db/downgrade.py base`.
- Critical indexes migration: `19c587b33197_add_critical_performance_indexes.py` (+ `temp_*` cleanup); apply low-traffic; baseline/post timings (monitoring perf command).
- Repair incomplete province metadata: `python scripts/util/backfill_province_metadata.py --province-id <id>` before auto-geometric delta pipelines.

## Handoff: enrichment bottleneck (`handoff_upsert_bottleneck.md`)
- Enrichment joins parcels to `municipalities` + `neighborhoods` for `municipality_id` + `region_id`.
- Evidence snapshot: `municipalities` 0 rows; `neighborhoods` 7; `parcels` 9007; all 9007 missing `municipality_id` or `region_id`.
- Queries cited: `SELECT COUNT(*) FROM municipalities|neighborhoods|parcels`; `SELECT COUNT(*) FROM parcels WHERE municipality_id IS NULL OR region_id IS NULL`.
- Root cause: empty `municipalities`; pipeline does not preload/verify reference data.
- Recommendations: pre-check reference tables; fail fast if missing; document sources/load steps.

## Pipeline uniqueness and upsert (`pipeline_table_uniqueness_review.md`)
- Upsert-enabled examples: `parcels_centroids.parcel_no`; `metro_stations.station_code`; `riyadh_bus_stations.station_code`; `qi_population_metrics.grid_id`; `qi_stripes.strip_id`.
- Replace mode (no unique / grouping issues historically): `metro_lines`, `bus_lines`; `neighborhoods_centroids` noted as problematic in older narrative.
- July 2025 update: `metro_stations` / `riyadh_bus_stations` geometry fixed to Point-only; `subdivision_id` int cast with string fallback; pipeline stable for handoff if tests pass.
- Table PK/upsert keys summarized: `parcels.parcel_objectid`; `parcels_centroids.parcel_no`; `neighborhoods.neighborhood_id`; `subdivisions.subdivision_id`; `metro_lines.id`; `bus_lines.id`; `metro_stations.station_code`; `riyadh_bus_stations.station_code`; `qi_population_metrics.grid_id`; `qi_stripes.strip_id`.
- Orchestrator/config: upsert only tables with unique constraints; see `WHAT_TO_DO_NEXT_PIPELINE_TABLES.md` for full action plan (referenced).

## Clean slate protocol (`CLEAN_SLATE_PROTOCOL.md`) — destructive local reset only
- WARNING: wipes local PostgreSQL/PostGIS data; dev-only.
- `brew services stop --all`; `brew uninstall postgresql postgresql@14 postgresql@15 postgis`.
- Remove data dirs: Apple Silicon `rm -rf /opt/homebrew/var/postgres*`; Intel `rm -rf /usr/local/var/postgres*`.
- `brew install postgis` (or pin `postgresql@14` + postgis); example `initdb --locale=C -E UTF-8 /opt/homebrew/var/postgresql@16`.
- `brew services start postgresql@16`; `createdb meshic -T template0`; `psql -d meshic -c "CREATE EXTENSION postgis;"`.
- Python: `python -m venv .venv && source .venv/bin/activate`; install alembic stack per doc.
- Alembic: init, configure, autogenerate initial revision, manual spatial index checks, `alembic upgrade head`.
- Verify: `psql -d meshic -c "\dt"`, `\d+ your_spatial_table`, `SELECT * FROM geometry_columns;`; run app tests.
