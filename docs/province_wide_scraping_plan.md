# Province-Wide Scraping Plan for Meshic Geospatial Pipeline

## 1  Overview
This document specifies the DB-driven approach for scraping **all six Saudi provinces** using Mapbox Vector Tiles (MVT) and persisting them into the Meshic PostGIS schema.

The plan addresses:
1. Centralised province metadata (now stored in the database)
2. Tile-list generation and storage in the `tile_urls` table
3. Downloader/orchestrator refactor for dynamic URLs and multi-province runs
4. CLI enhancements for simple user control
5. Database & performance considerations
6. Testing, documentation, and CI updates

---

## 2  Current State Snapshot
* **Downloader** – Async, accepts province and tile list from the database.
* **Tile discovery** – All tile discovery and orchestration is now managed via the `tile_urls` table in the database.
* **Province handling** – Province metadata is stored in the `provinces` table; tile URLs are generated and stored in `tile_urls`.
* **DB schema** – `tile_urls` table is the authoritative source for all tile processing.
* **Config** – Province-specific settings are loaded from the database.

Shortcomings for province-wide rollout (now resolved):
* Metadata is now centralised in the database.
* Automated full-bbox tile list for each province is generated and stored in `tile_urls`.
* Orchestrator supports multi-province and all-province runs.
* CLI supports "all-provinces" and multi-select flags.
* No more hard-coded province dicts or YAML-based tile lists.

---

## 3  Target Architecture
### 3.1 Province Metadata
* Province metadata is stored in the `provinces` table in the database.
* Tile URLs for each province are generated and stored in the `tile_urls` table.

### 3.2 Tile-List Generator
* Utility generates exhaustive list of tiles for each province and stores them in the database.
* Generator is independent; used by orchestrator or CLI tests.

### 3.3 Downloader Enhancements
* Accepts province and tile list from the database.
* Retains caching, retry, and concurrency controls.

### 3.4 Orchestrator Refactor
* Orchestrator queries the database for pending/failed tiles and processes them.
* Province-wide and all-province runs are now robust and resumable.

### 3.5 CLI UX
* `--province` (multi-use) and `--all-provinces` flags.
* Examples
  ```bash
  meshic-pipeline geometric --province riyadh
  meshic-pipeline geometric --all-provinces
  meshic-pipeline geometric --province riyadh --province makkah
  ```
* Help text updated accordingly.

### 3.6 Database & Performance Considerations
* **Schema** – `tile_urls` table is indexed for status and province.
* **Indices** – Confirm spatial & lookup indices on parcels, neighborhoods remain performant at scale (>1 M rows/province).
* **Chunking** – Keep 5 000-row chunks; adjust via settings if needed.
* **Caching** – Tiles are cached on disk for re-runs.
* **Resumability** – Track completed tiles per province to resume interrupted runs.

### 3.7 Testing Strategy
1. **Unit** – loader parses province metadata from DB, tile generator returns correct counts.
2. **Integration** – mock downloader per province; assert orchestrator iterates correctly.
3. **Performance** – profile memory & time for full Riyadh vs baseline.

### 3.8 Documentation & CI
* This doc (updated) reflects the DB-driven approach.
* README and CLI `--help` examples updated.
* CI job runs `meshic-pipeline geometric --province riyadh --limit-test` nightly.

---

## 4  Roll-Out Phases & Milestones
| Phase | Deliverable | Owner | Success Metric |
|-------|-------------|-------|----------------|
| 1 | Province metadata in DB, tile generator | Core Dev | DB parsed; 6 provinces recognised |
| 2 | Downloader & discovery refactor | Core Dev | Hotspot dict removed; dynamic URL works |
| 3 | Orchestrator & CLI multi-province support | Core Dev | `--all-provinces` runs end-to-end on small grid |
| 4 | Tests & CI green | QA | >90 % coverage on new code |
| 5 | Documentation & README updates | Tech Writer | Docs merged & reviewed |
| 6 | Full Riyadh validation | Data Ops | 1 M+ parcels ingested without errors |
| 7 | All provinces rollout | Data Ops | 6 M+ parcels, enrichment success ≥95 % |

---

## 5  Risk & Mitigation
| Risk | Impact | Mitigation |
|------|--------|-----------|
| Tile server rate limiting | Slows ingest | Maintain 0.05 s delay; exponential back-off |
| Memory pressure at large scale | OOM crash | Stream processing; monitor; scale DB chunk size |
| DB drift vs province list | Data mismatch | Validate DB province list at runtime |

---

## 6  Future Enhancements
* **Resume / checkpointing** – store processed tile list in DB or cache (now implemented).
* **Parallel province processing** – multiprocess at province granularity.
* **Dynamic boundary discovery** – auto-generate bbox at runtime (Phase 3 roadmap).

---

_Last updated: {{TODAY}}_ 