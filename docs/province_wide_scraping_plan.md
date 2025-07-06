# Province-Wide Scraping Plan for Meshic Geospatial Pipeline

## 1  Overview
This document specifies a robust, user-friendly approach for scraping **all six Saudi provinces** using Mapbox Vector Tiles (MVT) and persisting them into the Meshic PostGIS schema.

The plan addresses:
1. Centralised province metadata (bbox + URL templates)
2. Tile-list generation from bounding boxes
3. Downloader/orchestrator refactor for dynamic URLs and multi-province runs
4. CLI enhancements for simple user control
5. Database & performance considerations
6. Testing, documentation, and CI updates

---

## 2  Current State Snapshot
* **Downloader** – Async, accepts a single `base_url` and list of tiles.
* **Tile discovery** – Hot-spot logic or bbox→mercantile at runtime.
* **Province handling** – Hard-coded dict inside `EnhancedProvinceDiscovery`.
* **DB schema** – `provinces` table exists; no column for tile URLs.
* **Config** – `config.py` provides a global `tile_base_url`; province URLs are not externalised.

Shortcomings for province-wide rollout:
* Metadata scattered / duplicated.
* No automated full-bbox tile list for each province.
* Orchestrator limited to one province per run.
* CLI lacks "all-provinces" or multi-select flags.
* Hard-coded province dict is brittle.

---

## 3  Target Architecture
### 3.1 Province Metadata File
* **File:** `provinces.yaml`
* **Fields per province**
  ```yaml
  riyadh:
    display_name: "Riyadh"
    bbox_z15: {min_x: 20096, max_x: 20991, min_y: 13696, max_y: 14591}
    bbox_latlon:
      southwest: {lat: 19.31114, lon: 40.78125}
      northeast: {lat: 28.30438, lon: 50.625}
    tile_url_template: "https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf"
  ```
* Acts as single source of truth; easy to update without code changes.

### 3.2 Config Loader Extension
* `config.py` loads `provinces.yaml` at start-up.
* Exposes helper: `settings.get_province_meta("riyadh")`.

### 3.3 Tile-List Generator
* Utility converts `bbox_z15` into exhaustive list of `(15,x,y)`.
* Generator is independent; used by orchestrator or CLI tests.

### 3.4 Downloader Enhancements
* Accepts **dynamic** `base_url` per province.
* Retains caching, retry, and concurrency controls.

### 3.5 Discovery / Orchestrator Refactor
* Remove hard-coded hotspot dict; rely on `provinces.yaml`.
* `run_pipeline(..., provinces=["riyadh","makkah"], all_provinces=False)`
  * Loops through requested provinces.
  * Generates tile list via utility.
  * Sets province‐specific base URL for downloader.
* Adds summarised per-province metrics (tiles processed, parcels saved, failures).

### 3.6 CLI UX
* `--province` (multi-use) and `--all-provinces` flags.
* Examples
  ```bash
  meshic-pipeline geometric --province riyadh
  meshic-pipeline geometric --all-provinces
  meshic-pipeline geometric --province riyadh --province makkah
  ```
* Help text updated accordingly.

### 3.7 Database & Performance Considerations
* **Schema** – existing `province_id` FK sufficient; no DB changes required.
* **Indices** – confirm spatial & lookup indices on parcels, neighborhoods remain performant at scale (>1 M rows/province).
* **Chunking** – keep 5 000-row chunks; adjust via `settings.db_chunk_size` if needed.
* **Caching** – tiles are cached on disk for re-runs.
* **Resumability (future)** – track completed tiles per province to resume interrupted runs.

### 3.8 Testing Strategy
1. **Unit** – loader parses YAML, tile generator returns correct counts.
2. **Integration** – mock downloader per province; assert orchestrator iterates correctly.
3. **Performance** – profile memory & time for full Riyadh vs baseline.

### 3.9 Documentation & CI
* New doc (this file) added to `docs/`.
* README and CLI `--help` examples updated.
* CI job runs `meshic-pipeline geometric --province riyadh --limit-test` nightly.

---

## 4  Roll-Out Phases & Milestones
| Phase | Deliverable | Owner | Success Metric |
|-------|-------------|-------|----------------|
| 1 | `provinces.yaml`, loader, tile generator | Core Dev | YAML parsed; 6 provinces recognised |
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
| YAML drift vs DB province list | Data mismatch | Validate YAML vs `provinces` table at runtime |

---

## 6  Future Enhancements
* **Resume / checkpointing** – store processed tile list in DB or cache.
* **Parallel province processing** – multiprocess at province granularity.
* **Dynamic boundary discovery** – auto-generate bbox at runtime (Phase 3 roadmap).

---

## 7  Appendix A – Province Metadata Source (Authoritative JSON)
Included in project repository under `assets/province_bboxes.json` for traceability.

---

_Last updated: {{TODAY}}_ 