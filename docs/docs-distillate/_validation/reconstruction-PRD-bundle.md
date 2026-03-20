---
type: distillate-reconstruction
source_distillate: docs/docs-distillate/_index.md
reconstructed_from:
  - PRD.md
  - PROJECT_BRIEF.md
  - Delta_enrichment_PRD.md
  - ACCEPTANCE_CRITERIA.md
---

# Reconstruction: PRD, project brief, delta PRD, and acceptance themes

This document expands the **docs distillate** (requirements-and-product section and related bullets) into prose. It does not replace primary sources; where the distillate names a theme but not enough detail to reconstruct it faithfully, markers read **[POSSIBLE GAP]**.

## Product vision and domain

The initiative is a **production-grade PostGIS geospatial ETL and enrichment** system aimed at **Saudi Arabian parcel** data at **national scale**. Work spans ingesting vector tile geometry, persisting it in a canonical relational model, and enriching parcels using external APIs so downstream analytics and productized datasets stay consistent and repeatable.

The product framing ties **vector tiles and APIs** into a **single reliable PostGIS** store with **integrity, performance, and repeatable operations**. Strategically, the organization pursues **packaged data and analytics products** while **lowering operational cost** through **automation** and **resumable** processing.

## Scale, coverage, and ground truth

Distillate figures describe brownfield scale: **2.16M+ parcels**, **76M+ price metrics**, **130K+ building rules**, and **34,726 rows** in `tile_urls`. The project brief adds **coverage across 12 provinces**. For authoritative row counts and database naming, the distillate defers to **BROWNFIELD_PROJECT_DOCUMENTATION** over older or memory-bank-scale figures **[POSSIBLE GAP: exact reconciliation steps when brief vs. brownfield numbers differ]**.

## Pipeline concept (product view)

The pipeline is described as **two stages** with a clear contract: **geometry first**, then **enrichment**. Stage one moves from **tile discovery and orchestration** through **concurrent download**, **MVT decode**, **stitch and validate**, into **PostGIS**. Stage two applies **batch strategies**, calls **Suhail APIs** for transactions, building rules, and price metrics, **transforms** responses, and performs **relational upserts**.

Orchestration uses a **database-backed queue** on `tile_urls` with **row locking** and **`SKIP LOCKED`**, supporting **horizontally scalable**, **resumable workers**. The design emphasizes a **canonical schema**, **chunked database I/O**, and **adaptive concurrency**. **`temp_*` tables** are **ephemeral staging only**—no permanent dependency at rest, and safe to drop when idle.

## Geometric ingestion (functional themes)

Tiles are tracked with fields including **`url`**, **`zoom_level`**, **`x`**, **`y`**, **`status`**, **`retry_count`**, timestamps, and **error message**. Workers **claim tiles atomically** with locking and **`SKIP LOCKED`** for safe parallelism. HTTP is **async** with **retry and backoff**; MVT is decoded and geometries projected to **EPSG:4326**. The flow validates and stitches output, **enforces a canonical schema per layer**, and persists **per-layer stage output**. Seeding is **province-aware**, driven by **`provinces`** metadata such as **`bbox_z15`** and **tile URL templates**.

## Enrichment (functional themes)

Enrichment **strategies** include: **fast** (unprocessed parcels that already have price), **incremental** (stale by `enriched_at`), **full-refresh**, **universal metrics** (all parcels), and **delta** (comparison of fresh MVT transaction data against the production database). Processing uses **batching and upserts** with **idempotency**; successful runs update **`parcels.enriched_at`**, and **uniqueness constraints** must be maintained.

## Delta enrichment: vision, rules, and functional requirements

The delta vision is to **re-engineer delta processing** so only parcels with **meaningful transaction-data changes** are reprocessed, instead of re-running enrichment on unchanged parcels. Comparing **fresh MVT transaction data** to the **production DB** should **cut API cost, runtime, and latency**.

The business rule distilled here: **if and only if** a parcel’s **transaction data changed**, the system should call the **full set** of enrichment APIs—**transactions**, **price metrics**, and **building rules**—for that parcel. **Goals** include **80%+ reduction** in API and compute cost; **data freshness under 24 hours** for new transactions; a **single CLI** for the full delta workflow; **idempotent**, **robust** behavior with **clear errors**; and **strict TDD** for new logic.

Functional requirements as bullets in the distillate:

- **FR1:** The geometric pipeline can write parcels to a **temporary table** (with index); **`--save-as-temp`** on the geometric pipeline supports this.
- **FR2:** **Delta detection SQL** classifies changes as **`new`**, **`null_to_positive`**, **`zero_to_positive`**, **`price_changed`**; each detection triggers the **full enrichment API set** for that parcel.
- **FR3:** **`delta-enrich` CLI** automates the workflow and supports **`--auto-geometric`**.
- **FR4:** **Guaranteed cleanup** of temp tables even on failure.
- **FR5:** **Actionable, user-facing errors** without raw tracebacks.

Additional rules: delta detection **focuses on positive transaction price changes**; **negative** values may be stored but **do not trigger** enrichment. **Temp cleanup** applies when the table was created via **`--auto-geometric`**; **manually supplied** tables are **preserved**. CLI errors follow a **standard pattern**: red **`ERROR:`** prefix and yellow **`HINT:`** line. **`delta-enrich`** must log **structured metrics** (timestamp, duration, counts) and print a **concise summary** each run.

**[POSSIBLE GAP: full SQL specifications, exact exit-code matrix, and complete error catalog for delta and geometric CLIs.]**

## Alignment between main PRD and delta themes

The main PRD is said to support a **fresh MVT-derived table** (e.g. **`parcels_fresh_mvt`**) compared to **`parcels`**, with optional **automatic geometric stage** to create that table. **Change classification** should cover **new transactions**, **null→positive**, **zero→positive**, **price changed/disappeared**, plus a **run summary**. **Automatic cleanup** of the temporary fresh table is allowed.

## Configuration, CLI, and UX principles

Configuration uses **Pydantic** with **environment overrides**; **province metadata** loads from the **database at startup**. The **Typer** CLI covers **geometric**, **enrichment**, **composite province and country workflows**, **seeding**, and **monitoring**. Operational expectations: **clear help**, **safe defaults**, **idempotent** behaviors, **transparent logging**, and **run summaries**. **Arabic column normalization** and **consistent naming and schema mapping** across layers are required.

## Non-functional requirements

**Geometric throughput** targets **adaptive concurrency** with **>95% success** in a monitoring window and **configurable initial concurrency**. **Query latency** after index rollout: **p95 under 500ms** for common joins (e.g. parcels with neighborhoods; metrics by neighborhood and date). **Batch writes** use chunk defaults on the order of **5,000 rows** with **measured commit times**. The system relies on **idempotent upserts** and **conflict handling**, **retries** on transient HTTP and DB errors, **stale tile auto-recovery**, and **clear error messaging** with **status transitions**. **Structured logs**, **run summaries**, and **basic throughput and failure-rate metrics** are expected, along with **geometry validation**, **stitching consistency**, and **enrichment completeness** metrics. **Database credentials** must be secured; **PII** is limited to **business datasets**; **least-privilege database roles** are recommended.

## KPIs and success metrics

**PRD KPIs:** at least **95%** of parcels with **`transaction_price > 0`** should be **enriched**; at least **95%** **price metrics coverage** (parcel/neighborhood, monthly). **Brief MVP success** is slightly looser: **≥90%** of such parcels enriched. **Tile queue throughput** is measured as **tiles per hour** and **end-to-end time per province**. **Business metrics** include **coverage percentage**, **freshness** (median time from source to DB), **reliability** (successful run rate), and **alert mean time to repair**.

## MVP scope boundaries

**In scope for MVP:** **DB-driven geometric pipeline**; **enrichment strategies including delta**; **Alembic schema and performance indexes**; **operational CLI** for seeding, monitoring, and province/country workflows.

**Out of scope (brief):** **external client API**; **advanced analytics** (forecasting, clustering) beyond **core metrics**.

**Out of scope (PRD):** **end-user parcel browser UI**; **real-time streaming** (batch and near-real-time via delta instead); **multi-tenant portal** (future under an API epic).

## User journeys and personas

- **Data engineer:** seed provinces; run **`db_geometric`** with adaptive concurrency; monitor the queue; reset stale tiles; verify tables and indexes; run **`fast_enrich`** or **`delta_enrich`** on a daily cadence.
- **Ops / platform:** dashboards for throughput, errors, and stale tiles; alert thresholds; tune concurrency and batch sizes.
- **Analyst / PM:** coverage and freshness KPIs; release windows; requests to productize exports and APIs.

**[POSSIBLE GAP: detailed screen-by-screen or command-by-command runbooks for each persona beyond the bullets above.]**

## Epics (numbered backlog themes)

1. **Performance index rollout and query tuning** (Alembic; measured improvements).
2. **Monitoring and alerting** (KPIs, stale reset scheduler, basic alerts).
3. **Delta enrichment productization** (fresh-table lifecycle, summaries, change-type analytics, scheduling).
4. **Data quality framework** (completeness by province, outliers, validation, audits).
5. **API productization** (REST/GraphQL, auth, rate limits, export paths).
6. **Schema hygiene and normalization** (e.g. numeric typing for `building_rules`, redundancy reduction, migration plan).
7. **Documentation transition** (memory-bank → BMAD; brownfield doc as historical reference).

## Acceptance criteria (by epic)

### Epic 1 — Indexes and query performance

Production must contain the listed indexes (verified via **`pg_indexes`**): on **`parcels`**: **`neighborhood_id`**, **`province_id`**, **`ruleid`**; partial on **`transaction_price` WHERE transaction_price > 0**; **`enriched_at`**; composite **`(province_id, enriched_at)`**. On **`parcel_price_metrics`**: **`neighborhood_id`**; composites **`(metrics_type, year, month)`** and **`(neighborhood_id, metrics_type)`**. On **`transactions`**: **`transaction_date`**, **`transaction_price`**.

**p95 under 500ms** under representative load for: parcels↔neighborhoods join; parcels filtered by **`transaction_price > 0`** and **`enriched_at`**; time-series reads from **`parcel_price_metrics`** by **`(neighborhood_id, metrics_type, year, month)`**. Index migrations run via **Alembic without downtime**; **baseline and post-migration timings** are recorded and **linked in a runbook**.

### Epic 2 — Monitoring

**`meshic-pipeline monitor status`:** queue counts by status, top errors, age of oldest **`in_progress`**. **`recommend`:** scheduling guidance (next enrichment strategy, batch sizes). **`schedule-info`:** recommended cadence from freshness. A **scheduled job** resets stale **`in_progress`** after a **configurable threshold** (example **60 minutes**), logging the count affected. **Tiles per hour** and **enrichment counts per run** appear in logs, with **optional CSV or dashboard export**.

### Epic 3 — Delta productization

**Fresh MVT table name** is **configurable** (default **`parcels_fresh_mvt`**), created with **`--auto-geometric`**, dropped after a **successful** run. **Run summary** includes categories and counts: **new parcel with transaction**, **null→positive**, **zero→positive**, **price changed**, **price disappeared**—printed and logged; **exit code** reflects success or failure. A **documented delta schedule** (weekly/monthly) aligns with **monitoring recommendations**.

### Epic 4 — Data quality

**Coverage report:** percentage of parcels with **`neighborhood_id`**, **`province_id`**, **`enriched_at`**. **Outlier thresholds** for **`price_of_meter`** and **`transaction_price`** are defined and reported. Report path: **`docs/reports/data-quality-<date>.md`**.

### Epic 5 — API

**Documented REST or GraphQL** design with **auth** and **rate limits**. At least **one endpoint** by **`parcel_objectid`** and **one** by **`neighborhood_id`**. **p95 API reads** on indexed fields **under 500ms**; **pagination** and **error handling** documented; **sample requests** provided.

### Epic 6 — Schema hygiene

Migrate **`building_rules.max_building_coefficient`** and **`max_building_height`** to **DECIMAL**; align **`building_rules.zoning_id`** with **`parcels.zoning_id`** (**BIGINT**). A **normalization proposal** covers price metrics redundancy and FK standardization. **Alembic migrations** are tested in **staging** and applied to **production without data loss**.

### Epic 7 — Documentation

**BMAD Brief, PRD, Acceptance Criteria, and Tech Spec** are **authoritative**; **README** matches **production scale** and **CLI commands**. **Memory-bank** material is **labeled historical**; conflicting numbers are **reconciled or removed**.

## Constraints, assumptions, and risks

**Constraints:** API **rate limits and latency**; **network reliability**; **memory and I/O** on large province runs (mitigated by chunking and GC); **limited operational visibility** until monitoring is added.

**Assumptions:** **`provinces`** metadata is accurate (bbox, URL templates); enrichment **APIs are stable**; **`ON CONFLICT` upserts** suffice for idempotency.

**Risks:** performance without all recommended **indexes**; **stale tiles** stuck **`in_progress`** without automated resets; **data type inconsistencies** in **`building_rules`** complicating joins.

## Open questions

Finalize **production database name, ownership, and connection management**. Confirm **SLAs** for freshness and failure response. **Validate API quotas and backoff policies** at sustained national scale.

## Delta scope exclusions (delta PRD)

Out of delta PRD scope: **GUI**, **advanced query optimization**, **upstream MVT format changes**.

## Process and references (PRD metadata)

PRD author **Mary** (Business Analyst); date **2025-10-16**; project **level 2** (focused PRD plus solutioning handoff). Technical references named in the distillate include **`docs/BROWNFIELD_PROJECT_DOCUMENTATION.md`**, Alembic revision **`19c587b33197_add_critical_performance_indexes.py`**, **`src/meshic_pipeline/cli.py`**, **`models.py`**, and **`run_db_geometric.py`**.

## Index and distillate housekeeping

The distillate index notes that **dense bullet distillates** are split across three section files for LLM loading, and that some paths (**`TODO.md`**, **`Delta_enrichment_todo.md`**, templates, **`docs/reports/*`**, **`docs/archive/*`**) are **not** included in those section files but may still appear in **`docs/index.md`**. **[POSSIBLE GAP: full list of excluded files and whether they affect acceptance or scope.]**
