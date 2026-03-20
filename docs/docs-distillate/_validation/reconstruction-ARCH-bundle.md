---
type: distillate-reconstruction
source_distillate: docs/docs-distillate/_index.md
reconstructed_from:
  - ARCHITECTURE.md
  - brownfield-architecture.md
  - BROWNFIELD_PROJECT_DOCUMENTATION.md
---

# Reconstruction: architecture, brownfield architecture, and brownfield project documentation themes

This document expands the **docs distillate** (architecture-and-data section plus related bullets from stories, ops, and CLI distillates) into prose. Markers **[POSSIBLE GAP]** indicate insufficient detail in the distillate alone to reconstruct fully.

## System identity and scope

**Meshic / Suhail Final** is a **two-stage geospatial pipeline** for **Saudi Arabian parcel intelligence**: **MVT geometry** ingestion plus **Suhail API enrichment**. The lean architecture document is dated **2025-10-16**, version **0.1**; the brownfield document describes **current state**; the brownfield project documentation is dated **2025-10-16** (analyst Mary). An executive summary in production narrative cites **2.16M+ parcels**.

## Inputs, system of record, and control plane

**Inputs** are **province-specific Mapbox Vector Tiles (MVT)** and **Suhail APIs** for **transactions**, **building rules**, and **price metrics**. The **system of record** is **PostgreSQL with PostGIS**. The **control plane** is the **Typer** CLI **`meshic-pipeline`**.

## Stage 1: geometric pipeline (architecture)

The geometric stage performs **DB-queued tile downloads**, **decode**, **stitch**, **validate**, and **persist**, seeding from **`provinces.bbox_z15`** into **`tile_urls`**. Workers **claim** work with **`SELECT ... FOR UPDATE SKIP LOCKED`**, moving statuses **pending → in_progress → processed/failed**.

The **downloader** uses **aiohttp** with **concurrent fetch**, **retry**, and **backoff**. The **decoder** converts **MVT to EPSG:4326**. The **stitcher** uses **PostGIS dissolve** across tiles (**temporary tables**). The **persister** performs **schema-driven upsert**.

Implementation paths cited: **`src/meshic_pipeline/run_db_geometric.py`**, **`decoder/mvt_decoder.py`**, **`geometry/stitcher.py`**, **`persistence/postgis_persister.py`**, **`persistence/table_management.py`**. Brownfield also references **`run_geometric_pipeline.py`** for Stage 1 MVT processing **[POSSIBLE GAP: relationship and deprecation story between `run_db_geometric` and `run_geometric_pipeline`].**

End-to-end flow: **seed `tile_urls`** → **claim batch** → **fetch** → **decode** (with **Arabic column normalization**) → **validate CRS/geometry** → **stitch** → **persist temp then canonical** → **update queue** to processed or failed. **Adaptive geometric concurrency** is described as **5–20**; **multiple geometric workers** share the **`tile_urls`** queue. Brownfield project notes include roughly **0.05s delay between requests**, **chunked DB writes** around **5000 rows per batch**, and **garbage collection** triggers for large runs.

## Stage 2: enrichment pipeline (architecture)

**Five strategies** align across architecture and brownfield: **fast**, **incremental**, **full**, **universal-metrics**, and **delta**.

- **fast-enrich:** **`transaction_price > 0 AND enriched_at IS NULL`**.
- **incremental-enrich:** **`transaction_price > 0 AND enriched_at < now() - interval 'N days'`** (examples: **7 days** in CLI, **30 days** in a doc snippet) **[POSSIBLE GAP: single canonical default for N across envs and docs]**.
- **full-refresh:** **`transaction_price > 0`** without **`enriched_at`** filter.
- **universal-metrics:** **all parcels**, including those **without** **`transaction_price`**.
- **delta-enrich:** parcels with **changed transaction price** via **MVT comparison**; optional **auto geometric**; **FULL OUTER JOIN** of **`parcels`** vs **fresh table** on **`parcel_objectid`**.

The enrichment path uses an **API client** (batch/async), transforms **JSON → SQLAlchemy**, **upserts** with **conflict handling**, and updates **`parcels.enriched_at`**. Brownfield project documentation notes **`ON CONFLICT DO NOTHING`** on a persistence path **[POSSIBLE GAP: which tables and when DO NOTHING vs full upsert semantics apply]**.

Files: **`run_enrichment_pipeline.py`**, **`enrichment/strategies.py`**, **`enrichment/api_client.py`**, **`persistence/enrichment_persister.py`**; brownfield adds **`enrichment/processor.py`**, **`metrics_only_processor.py`**.

## Suhail HTTP surface

Endpoints named: **`/parcel/buildingRules`**; **`/api/parcel/metrics/priceOfMeter`**; **`/transactions`**; with **API key/session**, and **rate limiting** plus **retry/backoff** referenced. **[POSSIBLE GAP: request/response schemas, auth flow, and pagination rules.]**

## Queue model and stale protection

**`tile_urls`** includes **`id` PK**, **`url` UNIQUE**, **z/x/y**, **`status`**, **`retry_count`**, **`last_checked_at`**, **`error_message`**, and further columns implied by ellipsis in the distillate.

**`TileURL.claim_tiles_for_processing(..., SKIP LOCKED)`** and **`reset_stale_in_progress(..., stale_minutes=60)`** live in **`src/meshic_pipeline/persistence/models.py`**. **Stale protection** means **periodic reset** of stuck **`in_progress`** tiles; schedule example **`stale_minutes=60`**.

## Core relational schema (distilled)

- **`parcels`:** **`parcel_objectid` PK**, **geometry MULTIPOLYGON 4326**, **`transaction_price`**, **`enriched_at`**, **`neighborhood_id`**, **`province_id`**, **`ruleid`**, and **20+ attribute columns** cited without full enumeration.
- **`neighborhoods`:** **`neighborhood_id` PK**, **geometry**, **`province_id`**, …
- **`provinces`:** **`province_id` PK**, **geometry**, **`bbox_*`**, **`tile_server_url`**, **`province_name`**, **`province_name_ar`**, **`region_id`**, …
- **`transactions`:** **`transaction_id` PK**, **`parcel_objectid` FK**, **`transaction_price`**, **`price_of_meter`**, **`transaction_date`**, **`raw_data`**; unique **`(transaction_id, parcel_objectid)`** cited.
- **`parcel_price_metrics`:** **`metric_id` PK SERIAL**, **`parcel_objectid` FK**, **`neighborhood_id` FK**, **`metrics_type`**, **`year`**, **`month`**, **`average_price_of_meter`**; unique **`(parcel_objectid, month, year, metrics_type)`**.
- **`building_rules`:** **`(parcel_objectid, building_rule_id)` PK**, **`zoning_id`**, **`landuse`**, **`max_building_coefficient` VARCHAR**, **`max_building_height` VARCHAR**, **`raw_data` JSON**; unique **`(parcel_objectid, building_rule_id)`**.
- **`zoning_rules`:** **`ruleid` PK**.

## Supporting and temporary schema

**Supporting tables** named: **subdivisions**, **parcels_centroids**, **neighborhoods_centroids**, **metro_lines**, **metro_stations**, **bus_lines**, **riyadh_bus_stations**, **qi_population_metrics**, **qi_stripes**, **parcels_base**, **parcels_enriched**, **land_use_groups** (plus **zoning_rules**).

**Ephemeral pipeline temps:** **`temp_parcels`**, **`temp_neighborhoods`**, **`temp_subdivisions`**. Architecture states **`temp_*`** is **staging only** with **no persistent dependency at rest**; brownfield project documentation flags the **same names** as a **production schema pollution risk** if they appear outside controlled pipeline use.

## Production scale (ground-truth narrative)

**`parcels`:** **2,163,003** rows. **`parcel_price_metrics`:** **76,080,728** rows. **`transactions`:** **70,787** rows. **`building_rules`:** **130,112** rows. **`tile_urls`:** **34,726** rows; **processed 33,938 (97.7%)**; **`in_progress` 788 (2.3%)**. **`provinces`:** **12**; **`neighborhoods`:** **812**. Database name **`meshic`** (not **`meshic_pipeline`** as some documents suggest); owner **`postgres`**.

## Superseded and memory-bank figures

Brownfield architecture once cited **1M+ parcels**, **45K+ transactions**, **68K+ building rules**, **752K+ parcel_price_metrics**—**superseded** by ground-truth counts where they conflict. **Memory bank** figures (~**9,007** parcels, ~**200** metrics, **10** transactions, **0** building rules, “**3x3 grid**”) are **orders of magnitude smaller** than ground truth; tile coverage is described as roughly **3,858×** vs a “**3x3 test**” narrative.

## Indexes and Alembic

Alembic revision **`19c587b33197_add_critical_performance_indexes.py`** is the reference for **FK and business indexes** on **`parcels`**, **`parcel_price_metrics`**, and **`transactions`**. Before remediation, ground-truth documentation listed **missing critical indexes** (neighborhood, province, ruleid on parcels; neighborhood on metrics; partial transaction_price; enriched_at) with an **estimated 60–80% improvement** for common joins after application. **Composite `(province_id, enriched_at)`** and metrics composites **`(metrics_type, year, month)`**, **`(neighborhood_id, metrics_type)`** appear in the architecture index discussion.

## CLI surface (architecture inventory)

**Geometric:** **`geometric`**, **`province-geometric`**, **`saudi-arabia-geometric`**, **`db-geometric`** with **batch-size**, **concurrency**, **adaptive**, **strategies**, **recreate-db**, **bbox** options.

**Enrichment:** **`fast-enrich`**, **`incremental-enrich`**, **`full-refresh`**, **`universal-metrics`**, **`delta-enrich`** with **batch-size**, **limits**, **days-old**, **auto-geometric**, **fresh-table**, **show-details**.

**Composite:** **`smart-pipeline`**, **`province-pipeline`**, **`saudi-pipeline`**.

**Ops:** **`seed-tiles`** (province, provinces, region-slugs, stride, limit), **`discovery-summary`**, **`monitor status|recommend|schedule-info`**.

**Command count:** ground-truth doc states **18 commands in 5 categories**; brownfield architecture says **15+**; architecture lists a **representative subset** without a single total **[POSSIBLE GAP: authoritative canonical list and category mapping]**.

**Entry point:** **`src/meshic_pipeline/cli.py`**.

## Configuration (architecture)

**`src/meshic_pipeline/config.py`:** **Pydantic settings**; **DB URL**, **API endpoints**, **layers**, **batch sizes**; **provinces** loaded from DB via **`load_provinces_from_db`**; failure **falls back to empty provinces with warning**. **`pipeline_config.yaml`** plus **environment variables**. Example tile URL template: **`https://tiles.suhail.ai/maps/{slug}/{z}/{x}/{y}.vector.pbf`** (Riyadh example). **Secrets** in **`.env`**; **no secrets in code**; **least-privilege DB role**; **UTF-8 Arabic**.

## Technology stack

**Python 3.9+**; package **`meshic-pipeline` v0.1.0** per doc snippet; **SQLAlchemy 2.0+ async**; **GeoAlchemy2**; **GeoPandas**, **Shapely**, **h3**; **Alembic**; **Typer**; **aiohttp**; **mapbox-vector-tile/protobuf** for MVT.

## Repository layout

**`src/meshic_pipeline/`** — cli, config, decoder, discovery, downloader, enrichment, geometry, persistence, **`pipeline_orchestrator.py`**, utils; **`alembic/`**, **`tests/`**, **`scripts/`**, **`logs/`**, **`docs/`**, **`pyproject.toml`**.

## Non-functional targets (architecture)

**Geometric:** adaptive concurrency, minimal retries. **Query p95 < 500ms** post-index for core joins and metrics reads. **Idempotent upserts**; **resumable queue**; **horizontal scale** via **`SKIP LOCKED`**; **CLI monitoring**, **structured logs**, **run summaries**; **geometry validity** and **enrichment completeness by province**.

## Technical debt and risks (merged from brownfield/architecture)

- **CLI complexity:** some commands use **subprocess** instead of **direct imports**.
- **Memory:** **manual monitoring/GC** for very large runs.
- **Configuration:** **multiple sources** (YAML, Python, env).
- **Testing:** **pytest async** present; **coverage** described as **limited** vs pipeline complexity.
- **Containerization:** **none in repo** per brownfield architecture.
- **Schema debt:** **`building_rules`** numeric fields as **VARCHAR**; planned **DECIMAL/BIGINT** migrations; **`building_rules.zoning_id` INTEGER** vs **`parcels.zoning_id` BIGINT** inconsistency.
- **Risks:** **missing indexes**, **stuck `in_progress` tiles**, **API rate limits**, **outdated stakeholder docs**.

## Deployment and operations

**Dev, staging, prod** share **migrations**. **Local:** PostgreSQL+PostGIS, **`uv pip install -e .[dev]`**, **`meshic-pipeline`** execution, **`alembic upgrade head`**. **Temp table policy:** **pipeline-owned `temp_*` only**.

**Migrations (`docs/ops/migrations.md` themes):** Prereqs **`DATABASE_URL`** in **`.env`**; Postgres + PostGIS. Upgrade via **`python scripts/db/upgrade.py`** or **`alembic upgrade head`**. Downgrade via **`python scripts/db/downgrade.py -1`** or **`... base`**. Critical indexes migration includes **`temp_*` cleanup**; apply in **low-traffic** windows with **baseline/post timings**. **Repair incomplete province metadata** with **`python scripts/util/backfill_province_metadata.py --province-id <id>`** before **auto-geometric delta** pipelines.

## Roadmap and immediate actions (compressed)

**Near-term architecture:** index rollout, monitoring outputs, stale reset; then delta productization, data quality, schema hygiene; later API productization and dashboards/alerts. **Brownfield enhancements suggested:** Docker, web dashboard, expanded tests, simplified config, performance/memory tuning. **Ground-truth immediate actions:** apply **six critical indexes**; **drop temp tables** from prod if spurious; **update memory bank/README** counts and DB name; **audit enrichment coverage**; **investigate 788 `in_progress` tiles**; **add monitoring/alerting**.

## Data products and scheduling narrative

Outputs include **parcel boundaries**, **land use**, **zoning constraints**, **transaction history**, **price per m² analytics**, and **neighborhood/province linkage**. Optional schedules mentioned as narrative guidance: **daily fast-enrich**, **weekly incremental**, **monthly delta**, **quarterly full-refresh**.

## Brownfield handoff: enrichment bottleneck (themes)

Enrichment **joins parcels** to **`municipalities`** and **`neighborhoods`** for **`municipality_id`** and **`region_id`**. A cited snapshot had **`municipalities` 0 rows**, **`neighborhoods` 7**, **`parcels` 9007**, with **all 9007** missing **`municipality_id`** or **`region_id`**. **Root cause:** empty **`municipalities`**; pipeline **does not preload or verify** reference data. **Recommendations:** **pre-check reference tables**, **fail fast** if missing, **document sources and load steps**. **[POSSIBLE GAP: whether this snapshot still reflects production after later ground-truth counts.]**

## Pipeline uniqueness and upsert review (themes)

Upsert-enabled examples: **`parcels_centroids.parcel_no`**; **`metro_stations.station_code`**; **`riyadh_bus_stations.station_code`**; **`qi_population_metrics.grid_id`**; **`qi_stripes.strip_id`**. **Replace mode** (no unique / grouping issues historically): **`metro_lines`**, **`bus_lines`**; **`neighborhoods_centroids`** noted as problematic in an older narrative. **July 2025 update:** **`metro_stations`** / **`riyadh_bus_stations`** geometry fixed to **Point-only**; **`subdivision_id`** int cast with string fallback; pipeline stable for handoff **if tests pass**. PK/upsert keys summarized for multiple tables. Full action plan referenced in **`WHAT_TO_DO_NEXT_PIPELINE_TABLES.md`** **[POSSIBLE GAP: contents of that file not in distillate]**.

## Province-wide scraping and DB-driven MVT (themes)

**Authoritative** sources: **`provinces`** metadata; **`tile_urls`** list and status; **config from DB**; **no hard-coded province dicts** or YAML tile lists. **Downloader:** async; province and tiles from DB; caching, retry, concurrency; **resumable** multi/all-province. **CLI examples:** **`meshic-pipeline geometric --province riyadh`**; **`--all-provinces`**; multi **`--province`** flags. **Performance:** index **`tile_urls`** by status/province; spatial/lookup indices on parcels/neighborhoods at **>1M/province**; **~5000-row chunks**; **disk tile cache**. **CI suggestion:** nightly geometric with **`--province riyadh --limit-test`**. **Rollout phases** span metadata+generator through full Riyadh and six provinces with success metrics in a doc table **[POSSIBLE GAP: exact phase gates and metric table not reproduced here]**.

## CLI audit themes (documentation vs implementation)

Inventory includes flags such as **`--bbox`**, **`--recreate-db`**, **`--save-as-temp`** on geometric paths; batch and limit flags on enrich commands; **`delta-enrich`** options **`--fresh-table`**, **`--auto-geometric`**, **`--show-details`**; **`smart-pipeline`** with **`--geometric-first`**, **`--batch-size`**, **`--bbox`**. **Recommendations:** remove **legacy tile-discovery CLI refs**; **document all flags**; **standardize syntax**; improve **`--help`**; add **advanced/composite examples**.

## Clean slate protocol (destructive local reset only)

**Warning:** wipes **local** PostgreSQL/PostGIS data; **dev-only**. Steps include stopping Homebrew services, uninstalling Postgres/PostGIS variants, removing data directories (**Apple Silicon** vs **Intel** paths), reinstalling PostGIS/Postgres (example **`postgresql@16`**), **`createdb meshic`**, **`CREATE EXTENSION postgis`**, Python venv and Alembic workflow, verification queries. **[POSSIBLE GAP: full ordered checklist and version pinning policy for teams not on Homebrew/macOS.]**

## EPIC-001 cross-reference (performance and monitoring)

EPIC-001 scope: **Alembic critical indexes**; **baseline→post measurements**; **CLI monitoring** for tile queue and enrichment coverage; **automate stale tile resets**; **out of scope:** full **Prometheus/Grafana**. Migration **`19c587b33197_add_critical_performance_indexes.py`**: indexes plus **safe cleanup** of stray **`temp_*`**. Monitor commands expose **queue counts**, **failed count**, **oldest `in_progress` age**, enrichment **totals and percentages**. **`monitor recommend`** chooses next action among **fast-enrich / incremental / delta** with **batch sizes**. **`schedule-info`** suggests **daily/weekly/monthly** cadence from freshness. Acceptance mentions **`meshic-pipeline monitor reset-stale -- --stale-minutes 60`**; report naming variants (**`perf-post-<date>.md`** vs **`perf-post-index-*.md`**) appear across stories and AC **[POSSIBLE GAP: single standard report filename pattern]**.

## References cited in architecture distillate

**`docs/PRD.md`**, **`docs/PROJECT_BRIEF.md`**, **`docs/ACCEPTANCE_CRITERIA.md`**, **`docs/BROWNFIELD_PROJECT_DOCUMENTATION.md`**, **`alembic/versions/19c587b33197_add_critical_performance_indexes.py`**, **`cli.py`**, **`persistence/models.py`**.
