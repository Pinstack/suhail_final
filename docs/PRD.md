# Suhail Product Requirements Document (PRD): Meshic Geospatial Data Pipeline

Author: Mary (Business Analyst)
Date: 2025-10-16
Project Level: 2 (Focused PRD + solutioning handoff)
Project Type: Data Platform (Geospatial ETL + Enrichment)
Target Scale: National coverage (Saudi Arabia), 2.16M+ parcels

---

## Description, Context and Goals

A production-grade, database-driven geospatial pipeline that ingests Saudi Arabian parcel data from vector tiles, transforms and validates geometries, and enriches parcels with commercial datasets (transactions, zoning/building rules, and price metrics). The system persists data in a robust PostGIS schema optimized for analytics and downstream products.

### Deployment Intent

- Operate as a resilient, resumable data ingestion and enrichment service running on scheduled or continuous jobs.
- Support distributed workers against a DB queue for geometric processing, with separate enrichment workers.
- Provide operational CLIs for seeding, monitoring, and country/province workflows.

### Context

- Current reality (see docs/BROWNFIELD_PROJECT_DOCUMENTATION.md): 2.16M+ parcels processed, 76M+ price metrics, 130K+ building rules, 34,726 tiles orchestrated in DB (`tile_urls`).
- Architecture validated at production scale; key gaps are operational monitoring, index rollout consistency, and documentation alignment.
- Team is transitioning documentation from legacy memory-bank notes to BMAD artifacts.

### Goals

- Reliable national coverage with consistent, queryable PostGIS data.
- Fast delta updates using MVT change detection with measured SLAs.
- Operational visibility (throughput, failures, success rates) and alerting.
- Strong query performance via critical indexes and schema hygiene.

---

## Requirements

### Functional Requirements

1. Geometric Ingestion (Stage 1)
   - Maintain `tile_urls` table with fields: `url`, `zoom_level`, `x`, `y`, `status`, `retry_count`, timestamps, and error message.
   - Provide atomic tile claiming with row locking and `SKIP LOCKED` to support concurrent workers.
   - Async HTTP fetching with retry/backoff; decode Mapbox Vector Tiles; project geometries to EPSG:4326.
   - Validate and stitch geometries; enforce canonical schema per layer; write to PostGIS.
   - Persist per-layer stage output; no permanent dependency on `temp_*` tables (ephemeral staging only).
   - Province-aware seeding of `tile_urls` from `provinces` table metadata (bbox_z15, tile URL templates).

2. Enrichment (Stage 2)
   - Strategies: fast (unprocessed with price), incremental (stale by `enriched_at`), full-refresh, universal metrics (all parcels), delta (MVT vs DB price comparison).
   - Integrate Suhail APIs for transactions, building rules, and price metrics; handle batching and upserts with idempotency.
   - Update `parcels.enriched_at` upon successful writes; maintain uniqueness constraints.

3. Delta Enrichment
   - Support fresh MVT-derived table (e.g., `parcels_fresh_mvt`) to compare against `parcels`.
   - Optionally auto-run geometric stage to create fresh table.
   - Provide change classification (new transactions, null→positive, zero→positive, price changed/disappeared) and run summary.
   - Allow automatic cleanup of the temporary fresh table.

4. Monitoring & Operations
   - CLI to display queue status, recommendations, and schedule info.
   - Ability to reset stale `in_progress` tiles after configurable threshold.
   - Export basic run metrics (tiles processed per hour, enrichment counts, error rates).

5. Configuration & CLI
   - Pydantic-based config with environment overrides; province metadata loaded from DB at startup.
   - Typer CLI exposing geometric, enrichment, composite workflows (province/country), seeding, and monitoring commands.

### Non-Functional Requirements

- Performance
  - Geometric throughput: adaptive concurrency targeting >95% success in window; configurable initial concurrency.
  - Query latency (post-index rollout): p95 < 500 ms for common joins (parcels↔neighborhoods, metrics by neighborhood/date).
  - Batch DB writes with chunk size defaults (e.g., 5,000 rows) and measured commit times.
- Reliability & Resilience
  - Idempotent upserts with conflict handling; retries on transient HTTP and DB errors.
  - Stale tile auto-recovery; clear error messaging and status transitions.
- Scalability
  - Horizontal scaling via DB queue and `SKIP LOCKED` semantics; safe concurrent workers.
- Observability
  - Structured logs with run summaries; basic metrics for throughput and failure rates.
- Data Quality
  - Geometry validation; stitching consistency; completeness metrics for enrichment coverage.
- Security & Compliance
  - Secure DB credentials handling; no PII storage beyond business datasets; least-privilege DB roles recommended.

---

## User Journeys

- Data Engineer
  - Seeds tiles for selected provinces; runs `db_geometric` with adaptive concurrency; monitors queue; resets stale tiles as needed; verifies PostGIS tables and indexes; triggers `fast_enrich` or `delta_enrich` daily.
- Ops/Platform Engineer
  - Monitors dashboards (throughput, errors, stale tiles); sets alert thresholds; tunes worker concurrency and batch sizes.
- Analyst/PM
  - Reviews coverage and freshness KPIs; plans release windows; requests exports or API productization.

---

## UX Design Principles

- Operational CLIs with clear help, safe defaults, and idempotent behaviors.
- Transparent, actionable logging and summaries for each run.
- Consistent naming and schema mapping across layers; Arabic column normalization.

---

## Epics

1. Performance Index Rollout & Query Tuning
   - Apply and validate FK + composite indexes; document measured improvements; codify in Alembic.
2. Monitoring & Alerting
   - Add KPIs (tiles/hour, enrichment success, error rates); implement stale reset scheduler; basic alerts.
3. Delta Enrichment Productization
   - Standardize fresh-table lifecycle, summaries, and change-type analytics; scheduling.
4. Data Quality Framework
   - Completeness metrics by province; outlier detection; validation rules; periodic audits.
5. API/Productization
   - Define REST/GraphQL delivery for clients; auth/rate limits; data export pathways.
6. Schema Hygiene & Normalization
   - Numeric typing for building_rules; reduce redundancy; migration plan.
7. Documentation Transition
   - Migrate from memory-bank docs to BMAD artifacts; keep brownfield doc as historical reference.

Note: Epics guide solutioning and story creation; scope can be phased across sprints.

---

## Out of Scope

- End-user UI for browsing parcels (future product). 
- Real-time streaming ingestion; current design is batch/near-real-time via delta runs.
- Multi-tenant client portal (covered under API/Productization epic as future work).

---

## Next Steps

- Approve PRD scope and KPI targets.
- Execute index migration in production; capture before/after metrics.
- Implement baseline monitoring + stale reset schedule.
- Align documentation: update README and BMAD docs; retire memory-bank references.
- Handoff to architecture/tech-spec for Epics 1–3; prepare initial user stories.

---

## Document Status

- [ ] Goals and context validated with stakeholders
- [ ] All functional requirements reviewed
- [ ] User journeys cover all major personas
- [ ] Epic structure approved for phased delivery
- [ ] Ready for architecture phase

Note: See `docs/BROWNFIELD_PROJECT_DOCUMENTATION.md` and `docs/archive/legacy-root-md/DATABASE_ARCHITECTURE_ANALYSIS.md` for technical context.

---
