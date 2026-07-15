# Product Brief: Suhail Geospatial Data Pipeline

Date: 2025-10-16
Author: Mary (Business Analyst)
Status: Draft for PM Review

---

## Executive Summary

Suhail is a production-grade, DB-driven geospatial data pipeline that extracts, processes, and enriches Saudi Arabian land parcel data at national scale. The pipeline has processed 2.16M+ parcels across 12 provinces, generated 76M+ price metrics, and captured 130K+ building rules. A database-orchestrated tile queue (34,726 tiles) enables distributed, resumable geometric processing, followed by API-based enrichment (transactions, rules, price metrics). The system is ready for optimization and productization (monitoring, SLAs, client delivery interfaces).

---

## Problem Statement

Organizations require comprehensive, up-to-date, and spatially accurate parcel intelligence to power analytics and decision-making in the Saudi real estate market. Existing data sources (vector tiles, disparate APIs) must be unified into a reliable PostGIS schema with robust performance, data integrity, and operational repeatability across all provinces.

---

## Proposed Solution

- Two-stage pipeline:
  - Geometric: DB-driven tile discovery and orchestration → concurrent downloads → MVT decoding → stitching/validation → PostGIS persistence.
  - Enrichment: Batch strategies pull parcel IDs and call Suhail APIs (transactions, building rules, price metrics) → transform → upsert into relational tables.
- Database-orchestrated work queue via `tile_urls` with row-locking and retries; pipeline is fully resumable and horizontally scalable.
- Strong schema with spatial types and upsert patterns; critical performance indexes managed via Alembic migrations.

---

## Target Users

- Primary: Internal data engineering and analytics teams needing reliable, queryable geospatial datasets.
- Secondary: Client-facing analytics products and BI teams consuming exported datasets and aggregated market metrics.

---

## Goals and Success Metrics

- Business Objectives
  - Deliver province- and country-wide parcel intelligence to support commercial analytics products and revenue.
  - Reduce time-to-freshness for market updates; enable delta pipelines for near-real-time changes.
  - Provide high-reliability data products with documented SLAs.

- User Success Metrics
  - Coverage: % of parcels/geographies populated with core attributes and enrichment.
  - Freshness: Median time from new data availability to database persistence.
  - Reliability: Successful run rate; alert MTTR.

- KPIs (initial)
  - Parcels with transaction_price > 0 that are enriched: ≥ 95%.
  - Price metrics coverage (parcel/neighborhood, monthly): ≥ 95% of parcels.
  - Tile queue throughput: tiles/hour and end-to-end time per province.
  - Query performance: p95 for common joins under 500 ms after index rollout.

---

## Strategic Alignment and Financial Impact

- Financial Impact: Enables packaged data products and analytics services for clients; lowers data ops cost through automation and resumable processing.
- Company Objectives: Accelerate market coverage, power client-facing insights, and improve operational efficiency.
- Strategic Initiatives: Productize data delivery (APIs/exports), formalize monitoring/SLAs, expand advanced analytics (forecasting, hotspot detection).

---

## MVP Scope

- Core Features (Must Have)
  - DB-driven geometric pipeline (tile queue, decode, stitch, validate, persist to PostGIS).
  - Enrichment strategies: fast, incremental, full-refresh, universal metrics, delta.
  - Alembic migrations for schema + performance indexes.
  - Operational CLI for seeding, monitoring, and country/province workflows.

- Out of Scope for MVP
  - External client API product (post-MVP).
  - Advanced analytics (forecasting, clustering) beyond core metrics.

- MVP Success Criteria
  - Country-wide coverage with validated data in PostGIS.
  - Enrichment coverage ≥ 90% of parcels with transaction_price > 0.
  - Core queries performant post-indexes (FK + composite) with documented baselines.

---

## Post-MVP Vision

- Phase 2 Features
  - Production monitoring dashboards (tile throughput, enrichment success, errors) and alerting.
  - Automated recovery for stale in-progress tiles; scheduled delta runs.
  - Data quality framework (completeness, outliers, trend checks).

- Long-term Vision
  - Client-facing REST/GraphQL API with rate limits and webhooks.
  - Advanced spatial analytics (hotspots via H3, time-series forecasting).
  - Schema normalization to reduce redundancy and standardize types.

- Expansion Opportunities
  - Additional regions/markets; extended regulatory datasets; partner data overlays.

---

## Technical Considerations

- Platform Requirements
  - PostgreSQL 14+ with PostGIS; Python 3.9+; async I/O (aiohttp); SQLAlchemy 2.x; Typer CLI; Pydantic settings.

- Architecture Considerations
  - DB queue `tile_urls` with `SKIP LOCKED` and retries; resumable and parallelizable.
  - Two-stage pipeline with clear contracts (geometry → enrichment).
  - Canonical schema and schema-driven writes; chunked DB I/O and adaptive concurrency.
  - Temp tables are ephemeral staging only; safe to drop at rest (no persistent dependency).
  - Critical indexes applied via Alembic for FK + business queries.

---

## Constraints and Assumptions

- Constraints
  - External API rate limits/latency; network reliability.
  - Memory/IO constraints during large province runs; need chunking and GC.
  - Operational visibility currently limited (monitoring to be added).

- Assumptions
  - Province metadata is synced and accurate in `provinces` (bbox, tile URL templates).
  - Enrichment APIs remain stable; ON CONFLICT upserts sufficient for idempotency.

---

## Risks and Open Questions

- Key Risks
  - Performance without all recommended indexes in place.
  - Stale tiles stuck in `in_progress` without automated resets.
  - Data type inconsistencies (e.g., building_rules numeric fields) complicate joins.

- Open Questions
  - Finalize production DB name/ownership and connection management.
  - Confirm SLAs for freshness and failure response.
  - Validate API quotas and backoff policies at sustained national scale.

---

## Appendices

- References
  - docs/BROWNFIELD_PROJECT_DOCUMENTATION.md
  - `docs/archive/legacy-root-md/DATABASE_ARCHITECTURE_ANALYSIS.md`
  - alembic/versions/19c587b33197_add_critical_performance_indexes.py
  - src/suhail_pipeline/cli.py, src/suhail_pipeline/persistence/models.py, src/suhail_pipeline/run_db_geometric.py

---

Next Steps: Review with stakeholders, confirm KPIs/SLAs, and approve the short-term optimization plan (indexes, monitoring, stale-reset automation). 

