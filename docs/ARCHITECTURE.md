# Architecture: Suhail Geospatial Data Pipeline (Lean)

Date: 2025-10-16
Author: Mary (Business Analyst)
Status: v0.1 (Lean Architecture for Planning)

---

## 1. System Context

Suhail is a two-stage, production-grade data pipeline for Saudi Arabian parcel intelligence:

- Inputs
  - Province-specific Mapbox Vector Tiles (MVT) — geometry + attributes
  - Suhail APIs — transactions, building rules, price metrics
- Processing
  - Stage 1 Geometric: DB-queued tile downloads, decode, stitch, validate, persist
  - Stage 2 Enrichment: Batch parcel selection, API calls, transform, upsert
- Storage
  - PostgreSQL + PostGIS as system of record
- Control plane
  - Typer CLI for orchestration and monitoring

---

## 2. Core Components

- CLI (Typer)
  - `suhail-pipeline db-geometric`, `geometric`, `province-geometric`, `saudi-arabia-geometric`
  - `fast-enrich`, `incremental-enrich`, `full-refresh`, `universal-metrics`, `delta-enrich`
  - `seed-tiles`, `discovery-summary`, `monitor <status|recommend|schedule-info>`
  - File: `src/suhail_pipeline/cli.py`

- Discovery & Queue
  - `tile_urls` table stores z/x/y tile work items with statuses
  - Seeding via province bbox metadata (`provinces` table)
  - Model: `TileURL` with `claim_tiles_for_processing(..., SKIP LOCKED)` and `reset_stale_in_progress(...)`
  - Files: `src/suhail_pipeline/persistence/models.py`, `src/suhail_pipeline/cli.py`

- Geometric Workers (Stage 1)
  - Downloader: `aiohttp` concurrent fetch with retry/backoff
  - Decoder: `MVTDecoder` (Mapbox Vector Tile → EPSG:4326)
  - Validation: geometry sanity checks
  - Stitcher: PostGIS-based dissolve across tiles using temporary tables
  - Persister: Schema-driven writes, upsert support, temp table utilities
  - Files: `src/suhail_pipeline/run_db_geometric.py`, `.../decoder/mvt_decoder.py`, `.../geometry/stitcher.py`, `.../persistence/postgis_persister.py`, `.../persistence/table_management.py`

- Enrichment Workers (Stage 2)
  - Strategies: fast, incremental, full, universal metrics, delta
  - API client: Suhail endpoints; batch processing; async persistence
  - Files: `src/suhail_pipeline/run_enrichment_pipeline.py`, `.../enrichment/strategies.py`, `.../enrichment/api_client.py`, `.../persistence/enrichment_persister.py`

- Monitoring & Ops
  - CLI `monitor` subcommands; queue and enrichment visibility
  - Stale-tile reset via `TileURL.reset_stale_in_progress`
  - Files: `src/suhail_pipeline/run_monitoring.py`, `src/suhail_pipeline/persistence/models.py`

- Configuration
  - Pydantic settings; DB URL, API endpoints, layers, batch sizes
  - Province metadata loader (from DB) and tile server templates
  - File: `src/suhail_pipeline/config.py`

- Schema & Migrations
  - SQLAlchemy models (15+ tables)
  - Alembic migrations incl. critical performance indexes and temp-table cleanup
  - Files: `src/suhail_pipeline/persistence/models.py`, `alembic/versions/`

---

## 3. Data Flow

### Stage 1: Geometric (DB-Driven)
1) Seed tiles: `seed-tiles` populates `tile_urls` from `provinces` bbox_z15
2) Claim batch: workers `SELECT ... FOR UPDATE SKIP LOCKED` to mark `in_progress`
3) Fetch: `aiohttp` concurrent GET with retry/backoff
4) Decode: MVT → GeoDataFrames; cast types; Arabic column normalization
5) Validate: geometry checks, CRS enforcement
6) Stitch: PostGIS dissolve per ID across overlapping tiles (temp tables)
7) Persist: write to temp table per layer; then upsert or replace to canonical tables
8) Update queue: mark tiles `processed` or `failed` with error

### Stage 2: Enrichment
1) Select parcel IDs by strategy (fast/incremental/full/universal/delta)
2) Batch API calls (transactions, building rules, price metrics)
3) Transform JSON → SQLAlchemy models; upsert with conflict handling
4) Update `parcels.enriched_at`; emit run summaries

### Delta Enrichment
1) Create fresh MVT table (optional auto-run geometric)
2) FULL OUTER JOIN `parcels` vs fresh table on `parcel_objectid`
3) Filter change types (null→positive, price changed, etc.)
4) Enrich only changed parcels; drop fresh table on success

---

## 4. Data Model (Key Tables)

- `parcels(parcel_objectid PK, geometry, transaction_price, enriched_at, neighborhood_id, province_id, ruleid, ...)`
- `neighborhoods(neighborhood_id PK, geometry, province_id, ...)`
- `provinces(province_id PK, geometry, bbox_*, tile_server_url, ...)`
- `transactions(transaction_id PK, parcel_objectid FK, transaction_price, price_of_meter, transaction_date, raw_data)`
- `parcel_price_metrics(metric_id PK, parcel_objectid FK, neighborhood_id FK, metrics_type, year, month, average_price_of_meter)`
- `building_rules(parcel_objectid, building_rule_id) PK, zoning_id, numeric constraints, raw_data`
- `tile_urls(id PK, url UNIQUE, z/x/y, status, retry_count, last_checked_at, error_message)`
- `zoning_rules(ruleid PK)`

Indexes (via Alembic `19c587b33197...`):
- FKs: `parcels(neighborhood_id|province_id|ruleid)`, `parcel_price_metrics(neighborhood_id)`
- Business: partial on `parcels(transaction_price>0)`, `parcels(enriched_at)`, composite `(province_id,enriched_at)`
- Metrics: `parcel_price_metrics(metrics_type,year,month)`, `(neighborhood_id,metrics_type)`
- Transactions: `transactions(transaction_date)`, `transactions(transaction_price)`

---

## 5. Deployment & Topology

- Multiple geometric workers read from the same `tile_urls` queue; concurrency adaptive (5–20)
- Multiple enrichment workers run independently; DB is single source of truth
- All components share Postgres/PostGIS; Alembic manages schema
- Stale protection: periodic job resets stuck `in_progress` tiles
- Environments: dev/staging/prod with consistent migrations and settings

---

## 6. Non-Functional Requirements (Targets)

- Performance
  - Geometric: sustained throughput at adaptive concurrency; minimal retries
  - Query latency (post-index): p95 < 500 ms for core joins and metrics reads
- Reliability
  - Idempotent upserts; safe retries; resumable queue processing
- Scalability
  - Horizontal worker scaling via DB queue with `SKIP LOCKED`
- Observability
  - CLI monitoring outputs; structured logs; run summaries
- Data Quality
  - Geometry validity; enrichment completeness metrics by province
- Security
  - Secrets in `.env`; API keys via env; least-privilege DB user; UTF-8/Arabic support

---

## 7. Operations & Runbooks

- Seeding: `suhail-pipeline seed-tiles [--province|--region-slugs] [--limit|--stride]`
- Geometric run: `suhail-pipeline db-geometric --batch-size --concurrency --adaptive`
- Enrichment runs: `fast-enrich`, `incremental-enrich`, `full-refresh`, `universal-metrics`, `delta-enrich`
- Monitoring: `suhail-pipeline monitor status|recommend|schedule-info`
- Stale reset: schedule `TileURL.reset_stale_in_progress(..., stale_minutes=60)`
- Migrations: apply Alembic (indexes + hygiene) during low-traffic windows

Temp Table Policy
- `temp_*` tables are ephemeral staging surfaces created/dropped by the pipeline
- No persistent dependency on temp tables in production schema at rest

---

## 8. Security & Compliance

- Database URL and API keys loaded from environment; no secrets in code
- Principle of least privilege for DB roles
- Network egress to tile servers and Suhail APIs only; rate-limit posture defined in code

---

## 9. Risks & Mitigations

- Missing indexes degrade query performance → apply Alembic indexes; validate p95
- Stuck `in_progress` tiles → schedule stale reset; monitor queue age
- Data type inconsistencies (building_rules) → plan migrations (DECIMAL, BIGINT)
- API rate limits → backoff + concurrency caps; monitor error rates

---

## 10. Rollout & Backout

- Rollout
  - Validate migrations in staging; capture baseline timings
  - Apply to production; monitor latency; enable stale reset job
- Backout
  - Alembic downgrade for indexes if needed (not recommended)
  - Disable scheduled resets; revert CLI changes via version pin

---

## 11. Roadmap Alignment

- Near-term (Epic 1): Index rollout, monitoring outputs, stale reset
- Next: Delta productization, data quality reporting, schema hygiene
- Later: API productization, dashboards/alerts, schema normalization

---

## 12. References

- docs/PRD.md
- docs/PROJECT_BRIEF.md
- docs/ACCEPTANCE_CRITERIA.md
- docs/BROWNFIELD_PROJECT_DOCUMENTATION.md
- alembic/versions/19c587b33197_add_critical_performance_indexes.py
- src/suhail_pipeline/cli.py
- src/suhail_pipeline/persistence/models.py

