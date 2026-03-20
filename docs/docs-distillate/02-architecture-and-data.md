This section covers architecture, schema, and ground-truth production state. Part 2 of 3.

## Identity and scope
- Meshic / Suhail Final: two-stage geospatial pipeline for Saudi Arabian parcel intelligence (MVT geometry + Suhail API enrichment).
- Lean architecture doc dated 2025-10-16 v0.1; brownfield doc “current state”; brownfield project doc dated 2025-10-16 analyst Mary; production narrative cites 2.16M+ parcels in executive summary.

## Inputs and storage
- Inputs: province-specific Mapbox Vector Tiles (MVT); Suhail APIs (transactions, building rules, price metrics).
- System of record: PostgreSQL + PostGIS; control plane: Typer CLI `meshic-pipeline`.

## Stage 1 geometric
- DB-queued tile downloads, decode, stitch, validate, persist; seed from `provinces.bbox_z15` into `tile_urls`.
- Workers claim with `SELECT ... FOR UPDATE SKIP LOCKED`; statuses pending → in_progress → processed/failed.
- Downloader: aiohttp concurrent fetch with retry/backoff; decoder: MVT → EPSG:4326; stitcher: PostGIS dissolve across tiles (temp tables); persister: schema-driven upsert.
- Files: `src/meshic_pipeline/run_db_geometric.py`, `decoder/mvt_decoder.py`, `geometry/stitcher.py`, `persistence/postgis_persister.py`, `persistence/table_management.py`; brownfield also cites `run_geometric_pipeline.py` for Stage 1 MVT processing.
- Flow: seed `tile_urls` → claim batch → fetch → decode (Arabic column normalization) → validate CRS/geometry → stitch → persist temp then canonical → update queue processed/failed.
- Adaptive geometric concurrency 5–20; architecture doc: multiple geometric workers share `tile_urls` queue.
- Brownfield project doc: ~0.05s delay between requests; chunked DB writes ~5000 rows per batch; garbage collection triggers for large runs.

## Stage 2 enrichment
- Strategies: fast, incremental, full, universal-metrics, delta (architecture + brownfield align on five).
- fast-enrich: `transaction_price > 0 AND enriched_at IS NULL`.
- incremental-enrich: `transaction_price > 0 AND enriched_at < now() - interval 'N days'` (examples: 7 days CLI, 30 days in doc snippet).
- full-refresh: `transaction_price > 0` without enriched_at filter.
- universal-metrics: all parcels including those without transaction_price.
- delta-enrich: parcels with changed transaction_price via MVT comparison; optional auto geometric; FULL OUTER JOIN `parcels` vs fresh table on `parcel_objectid`.
- API client batch/async; transform JSON → SQLAlchemy; upsert with conflict handling; update `parcels.enriched_at`; brownfield project doc notes `ON CONFLICT DO NOTHING` on persistence path.
- Files: `src/meshic_pipeline/run_enrichment_pipeline.py`, `enrichment/strategies.py`, `enrichment/api_client.py`, `persistence/enrichment_persister.py`; brownfield adds `enrichment/processor.py`, `metrics_only_processor.py`.

## Suhail HTTP surface
- `/parcel/buildingRules`; `/api/parcel/metrics/priceOfMeter`; `/transactions`; API key/session; rate limiting and retry/backoff referenced.

## Queue and models
- `tile_urls(id PK, url UNIQUE, z/x/y, status, retry_count, last_checked_at, error_message, ...)`.
- `TileURL.claim_tiles_for_processing(..., SKIP LOCKED)` and `reset_stale_in_progress(..., stale_minutes=60)` in `src/meshic_pipeline/persistence/models.py`.
- Stale protection: periodic reset stuck in_progress tiles; schedule example stale_minutes=60.

## Core tables and keys
- `parcels(parcel_objectid PK, geometry MULTIPOLYGON 4326, transaction_price, enriched_at, neighborhood_id, province_id, ruleid, …)` — 20+ attribute columns cited.
- `neighborhoods(neighborhood_id PK, geometry, province_id, …)`.
- `provinces(province_id PK, geometry, bbox_*, tile_server_url, province_name, province_name_ar, region_id, …)`.
- `transactions(transaction_id PK, parcel_objectid FK, transaction_price, price_of_meter, transaction_date, raw_data)`; unique `(transaction_id, parcel_objectid)` cited.
- `parcel_price_metrics(metric_id PK SERIAL, parcel_objectid FK, neighborhood_id FK, metrics_type, year, month, average_price_of_meter)`; unique `(parcel_objectid, month, year, metrics_type)`.
- `building_rules(parcel_objectid, building_rule_id) PK, zoning_id, landuse, max_building_coefficient VARCHAR, max_building_height VARCHAR, raw_data JSON`; unique `(parcel_objectid, building_rule_id)`.
- `zoning_rules(ruleid PK)`.

## Supporting and temp schema
- Supporting tables named: subdivisions, parcels_centroids, neighborhoods_centroids, metro_lines, metro_stations, bus_lines, riyadh_bus_stations, qi_population_metrics, qi_stripes, parcels_base, parcels_enriched, land_use_groups (plus zoning_rules).
- Ephemeral pipeline temps: `temp_parcels`, `temp_neighborhoods`, `temp_subdivisions`; architecture: `temp_*` staging only, no persistent dependency at rest; brownfield project doc flags same names as production schema pollution risk.

## Production scale (ground-truth doc)
- `parcels`: 2,163,003 rows.
- `parcel_price_metrics`: 76,080,728 rows.
- `transactions`: 70,787 rows.
- `building_rules`: 130,112 rows.
- `tile_urls`: 34,726 rows; processed 33,938 (97.7%); in_progress 788 (2.3%).
- `provinces`: 12; `neighborhoods`: 812.
- Database name `meshic` (not `meshic_pipeline` as some docs); owner `postgres`.

## Older / alternate scale figures (deduped caveat)
- Brownfield architecture doc: 1M+ parcels, 45K+ transactions, 68K+ building rules, 752K+ parcel_price_metrics — superseded by ground-truth table counts where they conflict.

## Documentation vs memory bank
- Memory bank claimed ~9,007 parcels, ~200 price metrics, 10 transactions, 0 building rules, “3x3 grid”; ground truth ~240×–380,000× larger on key tables; tile coverage ~3,858× vs “3x3 test” narrative.

## Indexes and migrations
- Alembic revision `19c587b33197_add_critical_performance_indexes.py` referenced for FK and business indexes on `parcels`, `parcel_price_metrics`, `transactions`.
- Ground-truth doc listed missing critical indexes before remediation: `idx_parcels_neighborhood_id`, `idx_parcels_province_id`, `idx_parcels_ruleid`, `idx_parcel_price_metrics_neighborhood_id`, partial `idx_parcels_transaction_price` WHERE `transaction_price > 0`, `idx_parcels_enriched_at`; estimated 60–80% improvement for common joins after application.
- Composite `(province_id, enriched_at)` and metrics `(metrics_type,year,month)`, `(neighborhood_id,metrics_type)` noted in architecture index section.

## CLI surface
- Geometric: `geometric`, `province-geometric`, `saudi-arabia-geometric`, `db-geometric` with batch-size, concurrency, adaptive, strategies, recreate-db, bbox options.
- Enrichment: `fast-enrich`, `incremental-enrich`, `full-refresh`, `universal-metrics`, `delta-enrich` with batch-size, limits, days-old, auto-geometric, fresh-table, show-details.
- Composite: `smart-pipeline`, `province-pipeline`, `saudi-pipeline`.
- Ops: `seed-tiles` (province, provinces, region-slugs, stride, limit), `discovery-summary`, `monitor status|recommend|schedule-info`.
- Command count: ground-truth doc states 18 commands in 5 categories; brownfield architecture says 15+; architecture lists representative subset without total.
- Entry: `src/meshic_pipeline/cli.py`.

## Configuration
- `src/meshic_pipeline/config.py`: Pydantic settings; DB URL, API endpoints, layers, batch sizes; provinces loaded from DB via `load_provinces_from_db`; failure falls back to empty provinces with warning.
- `pipeline_config.yaml` + environment variables; province tile URL template pattern `https://tiles.suhail.ai/maps/{slug}/{z}/{x}/{y}.vector.pbf` (Riyadh example in doc).
- Secrets: `.env`; no secrets in code; least-privilege DB role; UTF-8 Arabic.

## Tech stack
- Python 3.9+; package `meshic-pipeline` v0.1.0 per doc snippet; SQLAlchemy 2.0+ async; GeoAlchemy2; GeoPandas, Shapely, h3; Alembic; Typer; aiohttp; mapbox-vector-tile/protobuf for MVT.

## Repo layout
- `src/meshic_pipeline/` cli, config, decoder, discovery, downloader, enrichment, geometry, persistence, `pipeline_orchestrator.py`, utils; `alembic/`, `tests/`, `scripts/`, `logs/`, `docs/`, `pyproject.toml`.

## NFR targets (architecture)
- Geometric: adaptive concurrency, minimal retries; query p95 < 500 ms post-index for core joins/metrics reads.
- Idempotent upserts; resumable queue; horizontal scale via SKIP LOCKED; CLI monitoring, structured logs, run summaries; geometry validity and enrichment completeness by province.

## Technical debt and risks (merged)
- CLI complexity: some commands use subprocess instead of direct imports.
- Memory: manual monitoring/GC for very large runs.
- Multiple configuration sources (YAML, Python, env).
- Testing: pytest async present; coverage described as limited vs pipeline complexity.
- No containerization in repo per brownfield architecture.
- `building_rules` numeric fields VARCHAR; plan DECIMAL/BIGINT migrations; `building_rules.zoning_id` INTEGER vs `parcels.zoning_id` BIGINT inconsistency noted.
- Risks: missing indexes, stuck in_progress tiles, API rate limits, outdated stakeholder docs.

## Deployment and ops
- Dev/staging/prod with shared migrations; local: PostgreSQL+PostGIS, `uv pip install -e .[dev]`, `meshic-pipeline` execution; `alembic upgrade head`.
- Temp table policy: pipeline-owned `temp_*` only.

## Roadmap and recommendations (compressed)
- Near-term architecture: index rollout, monitoring outputs, stale reset; then delta productization, data quality, schema hygiene; later API productization, dashboards/alerts.
- Brownfield enhancements suggested: Docker, web dashboard, expand tests, simplify config, performance/memory tuning.
- Ground-truth immediate actions: apply six critical indexes; drop temp tables from prod if spurious; update memory bank/README counts and DB name; audit enrichment coverage; investigate 788 in_progress tiles; add monitoring/alerting.

## Data products and freshness (ground-truth doc)
- Outputs: parcel boundaries, land use, zoning constraints, transaction history, price/m² analytics, neighborhood/province linkage; optional schedules: daily fast-enrich, weekly incremental, monthly delta, quarterly full-refresh (as narrative guidance).

## References cited in architecture
- `docs/PRD.md`, `docs/PROJECT_BRIEF.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/BROWNFIELD_PROJECT_DOCUMENTATION.md`, `alembic/versions/19c587b33197_add_critical_performance_indexes.py`, `cli.py`, `persistence/models.py`.
