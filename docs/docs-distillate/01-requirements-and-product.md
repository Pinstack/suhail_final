This section covers requirements, product scope, and acceptance themes. Part 1 of 3.

## Product and scale
- Production-grade PostGIS geospatial ETL + enrichment for Saudi Arabian parcels (national scale).
- Brownfield scale cited: 2.16M+ parcels, 76M+ price metrics, 130K+ building rules, 34,726 tiles in `tile_urls`.
- Brief adds: coverage across 12 provinces.
- Problem: unify vector tiles and APIs into reliable PostGIS with integrity, performance, repeatable ops.
- Strategic: packaged data/analytics products, lower ops cost via automation and resumable processing.

## Pipeline architecture
- Stage 1 geometric: tile discovery/orchestration → concurrent download → MVT decode → stitch/validate → PostGIS.
- Stage 2 enrichment: batch strategies; Suhail APIs for transactions, building rules, price metrics; transform; relational upserts.
- DB-orchestrated queue on `tile_urls` with row locking and `SKIP LOCKED`; horizontally scalable, resumable workers.
- Two-stage contract: geometry then enrichment; canonical schema; chunked DB I/O and adaptive concurrency.
- `temp_*` tables are ephemeral staging only; no permanent dependency; safe to drop at rest.

## Geometric ingestion (functional)
- `tile_urls` fields: `url`, `zoom_level`, `x`, `y`, `status`, `retry_count`, timestamps, error message.
- Atomic tile claiming with row locking and `SKIP LOCKED` for concurrent workers.
- Async HTTP with retry/backoff; decode MVT; project geometries to EPSG:4326.
- Validate and stitch; enforce canonical schema per layer; persist per-layer stage output.
- Province-aware seeding from `provinces` metadata (`bbox_z15`, tile URL templates).

## Enrichment (functional)
- Strategies: fast (unprocessed with price), incremental (stale by `enriched_at`), full-refresh, universal metrics (all parcels), delta (MVT vs DB price comparison).
- Batching and upserts with idempotency; update `parcels.enriched_at` on success; maintain uniqueness constraints.

## Delta enrichment (vision and FR)
- Re-engineer delta to process only parcels with meaningful transaction-data changes vs re-processing unchanged parcels.
- Compare fresh MVT transaction data to production DB to cut API cost, runtime, and latency.
- Rule: if and only if a parcel’s transaction data changed, call all enrichment APIs (transactions, price metrics, building rules) for that parcel.
- Goals: reduce costs 80%+ (API, compute); data freshness <24h for new transactions; one CLI for full delta workflow; idempotent, robust, clear errors; strict TDD for new logic.
- FR1: geometric pipeline can write parcels to a temp table (with index); `--save-as-temp` in geometric pipeline.
- FR2: delta detection SQL finds change types `new`, `null_to_positive`, `zero_to_positive`, `price_changed`; each detected change triggers full enrichment API set for that parcel.
- FR3: `delta-enrich` CLI automates workflow; supports `--auto-geometric`.
- FR4: guaranteed temp table cleanup even on failure.
- FR5: actionable user-facing errors; no raw tracebacks.
- Delta detection focuses on positive transaction price changes; negative values stored but do not trigger enrichment.
- Temp cleanup: only when table created via `--auto-geometric`; manually supplied tables preserved.
- CLI errors: standard pattern with red “ERROR:” prefix and yellow “HINT:” line (per Delta PRD).
- `delta-enrich` must log structured metrics (timestamp, duration, counts) and print concise summary each run.

## PRD delta alignment (main PRD)
- Support fresh MVT-derived table (e.g. `parcels_fresh_mvt`) compared to `parcels`.
- Optionally auto-run geometric stage to create fresh table.
- Change classification includes: new transactions, null→positive, zero→positive, price changed/disappeared, plus run summary.
- Allow automatic cleanup of temporary fresh table.

## Configuration, CLI, UX principles
- Pydantic config with environment overrides; province metadata from DB at startup.
- Typer CLI: geometric, enrichment, composite province/country workflows, seeding, monitoring.
- Operational CLIs: clear help, safe defaults, idempotent behaviors; transparent logging and run summaries.
- Arabic column normalization; consistent naming/schema mapping across layers.

## Non-functional requirements
- Geometric throughput: adaptive concurrency targeting >95% success in window; configurable initial concurrency.
- Query latency post-index rollout: p95 <500ms for common joins (parcels↔neighborhoods; metrics by neighborhood/date).
- Batch writes: chunk defaults e.g. 5,000 rows; measured commit times.
- Idempotent upserts and conflict handling; retries on transient HTTP and DB errors.
- Stale tile auto-recovery; clear error messaging and status transitions.
- Structured logs with run summaries; basic throughput and failure-rate metrics.
- Geometry validation, stitching consistency, enrichment completeness metrics.
- Secure DB credentials; no PII beyond business datasets; least-privilege DB roles recommended.

## KPIs and success metrics
- PRD KPI: ≥95% parcels with `transaction_price` > 0 that are enriched.
- PRD KPI: ≥95% price metrics coverage (parcel/neighborhood, monthly).
- Brief MVP success: ≥90% parcels with `transaction_price` > 0 enriched.
- Tile queue throughput: tiles/hour and end-to-end time per province.
- Business: coverage % and freshness (median time source→DB); reliability (successful run rate, alert MTTR).

## MVP scope boundaries
- MVP in: DB-driven geometric pipeline; enrichment strategies including delta; Alembic schema + performance indexes; operational CLI for seeding/monitoring/province/country workflows.
- MVP out (Brief): external client API; advanced analytics (forecasting, clustering) beyond core metrics.
- PRD out of scope: end-user parcel browser UI; real-time streaming (batch/near-real-time via delta); multi-tenant portal (future under API epic).

## User journeys (personas)
- Data engineer: seed provinces; run `db_geometric` with adaptive concurrency; monitor queue; reset stale tiles; verify tables/indexes; run `fast_enrich` or `delta_enrich` daily.
- Ops/platform: dashboards for throughput/errors/stale tiles; alert thresholds; tune concurrency and batch sizes.
- Analyst/PM: coverage and freshness KPIs; release windows; exports/API productization requests.

## Epics (numbered backlog themes)
- Epic 1: performance index rollout and query tuning (Alembic; measured improvements).
- Epic 2: monitoring and alerting (KPIs, stale reset scheduler, basic alerts).
- Epic 3: delta enrichment productization (fresh-table lifecycle, summaries, change-type analytics, scheduling).
- Epic 4: data quality framework (completeness by province, outliers, validation, audits).
- Epic 5: API/productization (REST/GraphQL, auth, rate limits, export paths).
- Epic 6: schema hygiene and normalization (e.g. numeric typing for `building_rules`, redundancy reduction, migration plan).
- Epic 7: documentation transition (memory-bank → BMAD; brownfield doc as historical reference).

## Acceptance: indexes and query performance (Epic 1)
- Indexes exist in production (verify `pg_indexes`): `parcels(neighborhood_id)`, `parcels(province_id)`, `parcels(ruleid)`; `parcel_price_metrics(neighborhood_id)`; partial `parcels(transaction_price) WHERE transaction_price > 0`; `parcels(enriched_at)`; composite `parcels(province_id, enriched_at)`; `transactions(transaction_date)`, `transactions(transaction_price)`; `parcel_price_metrics(metrics_type, year, month)` and `(neighborhood_id, metrics_type)`.
- p95 <500ms under representative load for: parcels↔neighborhoods join; parcels filtered by `transaction_price > 0` and `enriched_at`; time-series reads from `parcel_price_metrics` by `(neighborhood_id, metrics_type, year, month)`.
- Index migrations via Alembic without downtime; baseline and post-migration timings recorded and linked in runbook.

## Acceptance: monitoring (Epic 2)
- `suhail-pipeline monitor status`: queue counts by status, top errors, age of oldest `in_progress`.
- `suhail-pipeline monitor recommend`: scheduling guidance (next enrichment strategy, batch sizes).
- `suhail-pipeline monitor schedule-info`: recommended cadence from freshness.
- Scheduled job resets stale `in_progress` after configurable threshold (example 60 minutes); log count affected.
- Tiles/hour and enrichment counts per run in logs; optional CSV or dashboard export.

## Acceptance: delta productization (Epic 3)
- Fresh MVT table name configurable (default `parcels_fresh_mvt`); created with `--auto-geometric`, dropped after successful run.
- Run summary: categories and counts including new parcel with transaction, null→positive, zero→positive, price changed, price disappeared; printed and logged; exit code reflects success/failure.
- Documented delta schedule (weekly/monthly) aligned with monitoring recommendations.

## Acceptance: data quality (Epic 4)
- Coverage report: % parcels with `neighborhood_id`, `province_id`, `enriched_at`.
- Outlier thresholds for `price_of_meter` and `transaction_price` defined and reported.
- Report path: `docs/reports/data-quality-<date>.md`.

## Acceptance: API (Epic 5)
- Documented REST or GraphQL design with auth and rate limits.
- At least one endpoint by `parcel_objectid` and one by `neighborhood_id`.
- p95 API reads on indexed fields <500ms; pagination and error handling documented; sample requests.

## Acceptance: schema hygiene (Epic 6)
- Migrate `building_rules.max_building_coefficient` and `max_building_height` to DECIMAL; align `building_rules.zoning_id` with `parcels.zoning_id` (BIGINT).
- Normalization proposal for price metrics redundancy and FK standardization.
- Alembic migrations tested in staging; production apply without data loss.

## Acceptance: documentation (Epic 7)
- BMAD Brief, PRD, Acceptance Criteria, Tech Spec are authoritative; README matches production scale and CLI commands.
- Memory-bank labeled historical; conflicting numbers reconciled or removed.

## Platform and stack
- PostgreSQL 14+ with PostGIS; Python 3.9+; aiohttp; SQLAlchemy 2.x; Typer; Pydantic settings.

## Constraints and assumptions
- Constraints: API rate limits/latency; network reliability; memory/IO on large province runs (chunking/GC); limited operational visibility until monitoring added.
- Assumptions: `provinces` metadata accurate (bbox, URL templates); enrichment APIs stable; `ON CONFLICT` upserts sufficient for idempotency.

## Risks
- Performance risk without all recommended indexes.
- Stale tiles stuck `in_progress` without automated resets.
- Data type inconsistencies in `building_rules` complicate joins.

## Open questions
- Finalize production DB name/ownership and connection management.
- Confirm SLAs for freshness and failure response.
- Validate API quotas and backoff policies at sustained national scale.

## Delta scope exclusions
- Out of delta PRD scope: GUI, advanced query optimization, upstream MVT format changes.

## PRD process and references
- PRD author Mary (Business Analyst); date 2025-10-16; project level 2 (focused PRD + solutioning handoff).
- Technical references: `docs/BROWNFIELD_PROJECT_DOCUMENTATION.md`, `docs/archive/legacy-root-md/DATABASE_ARCHITECTURE_ANALYSIS.md`, Alembic index migration `19c587b33197_add_critical_performance_indexes.py`, `src/suhail_pipeline/cli.py`, `models.py`, `run_db_geometric.py`.
