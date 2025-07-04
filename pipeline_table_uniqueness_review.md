# Pipeline Table Uniqueness & Upsert/Replace Review (July 2025)

## Current State (Post-Migration & Pipeline Test)

### Tables with Unique Constraints (Upsert Enabled)
- **parcels_centroids.parcel_no**: Unique constraint added, upsert works
- **metro_stations.station_code**: Unique constraint added, upsert attempted (geometry type mismatch issue)
- **riyadh_bus_stations.station_code**: Unique constraint added, upsert works
- **qi_population_metrics.grid_id**: Unique constraint added, upsert works
- **qi_stripes.strip_id**: Unique constraint added, upsert works

### Tables in Replace Mode (No Unique Constraint)
- **metro_lines**
- **bus_lines**
- **neighborhoods_centroids** (no unique id column)
- Any other table not listed above

### Known Issues
- **neighborhoods_centroids**: No `neighborhood_id` column exists; pipeline and migration skip/err on this layer.
- **metro_stations**: Geometry type mismatch (Polygon vs. Point) during upsert; upsert fails for this table until data/schema are aligned.
- **metro_lines, bus_lines**: Pipeline attempts to group by None (no id column), resulting in errors; replace mode is correct, but code needs to skip grouping.

### Recent Changes
- Config and orchestrator updated to only upsert tables with unique constraints (see WHAT_TO_DO_NEXT_PIPELINE_TABLES.md)
- Alembic migration applied: unique constraints added to all upsertable tables/columns that exist
- Pipeline tested: upsert/replace logic confirmed for most tables

### Next Steps
- Update pipeline code to:
  - Skip or handle layers where the expected ID column does not exist
  - Ensure geometry types match schema for upsertable tables
  - Avoid grouping by None for replace-mode tables
- Communicate these issues and fixes to the team
- See WHAT_TO_DO_NEXT_PIPELINE_TABLES.md for the full action plan and rationale

## July 2025 Update: Geometry & Type Casting Issues Resolved

- Geometry type mismatches for `metro_stations` and `riyadh_bus_stations` are fully resolved: only Point geometries are written to the database for these layers.
- `subdivision_id` is now robustly handled: values are cast to integer where possible, and fallback to string with a warning if not. No pipeline interruptions or excessive warnings occur.
- All other layers process as expected.
- The pipeline is now stable, robust, and ready for further development, production runs, or handoff.
- **Merge to main is now appropriate if all tests pass.**

---

## Table of Contents
- [Overview](#overview)
- [Table-by-Table Review](#table-by-table-review)
- [Summary Table](#summary-table)
- [Key Considerations](#key-considerations)

---

## Overview
The pipeline ingests spatial and attribute data from third-party vector tiles and writes to a set of PostGIS tables. Some tables are suitable for upsert (INSERT ... ON CONFLICT), while others are not due to lack of a unique key or their data structure.

---

## Table-by-Table Review

### 1. **parcels**
- **Schema:**
  - `parcel_objectid` (PK, bigint)
  - ... (other fields)
- **Uniqueness:** Yes (primary key: `parcel_objectid`)
- **Recommendation:** Upsert supported (ON CONFLICT on `parcel_objectid`)

### 2. **parcels_centroids**
- **Schema:**
  - `parcel_no` (PK, string)
  - ...
- **Uniqueness:** Yes (primary key: `parcel_no`)
- **Recommendation:** Upsert supported (ON CONFLICT on `parcel_no`)

### 3. **neighborhoods**
- **Schema:**
  - `neighborhood_id` (PK, bigint)
  - ...
- **Uniqueness:** Yes (primary key: `neighborhood_id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `neighborhood_id`)

### 4. **neighborhoods_centroids**
- **Schema:**
  - `id` (PK, int)
  - ...
- **Uniqueness:** Yes (primary key: `id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `id`)

### 5. **subdivisions**
- **Schema:**
  - `subdivision_id` (PK, bigint)
  - ...
- **Uniqueness:** Yes (primary key: `subdivision_id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `subdivision_id`)

### 6. **metro_lines**
- **Schema:**
  - `id` (PK, int)
  - ...
- **Uniqueness:** Yes (primary key: `id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `id`)

### 7. **bus_lines**
- **Schema:**
  - `id` (PK, int)
  - ...
- **Uniqueness:** Yes (primary key: `id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `id`)

### 8. **metro_stations**
- **Schema:**
  - `station_code` (PK, string)
  - ...
- **Uniqueness:** Yes (primary key: `station_code`)
- **Recommendation:** Upsert supported (ON CONFLICT on `station_code`)

### 9. **riyadh_bus_stations**
- **Schema:**
  - `station_code` (PK, string)
  - ...
- **Uniqueness:** Yes (primary key: `station_code`)
- **Recommendation:** Upsert supported (ON CONFLICT on `station_code`)

### 10. **qi_population_metrics**
- **Schema:**
  - `grid_id` (PK, string)
  - ...
- **Uniqueness:** Yes (primary key: `grid_id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `grid_id`)

### 11. **qi_stripes**
- **Schema:**
  - `strip_id` (PK, string)
  - ...
- **Uniqueness:** Yes (primary key: `strip_id`)
- **Recommendation:** Upsert supported (ON CONFLICT on `strip_id`)

---

## Summary Table

| Table                  | Unique Key(s)         | Upsert Supported? | Notes                       |
|------------------------|-----------------------|-------------------|-----------------------------|
| parcels                | parcel_objectid       | Yes               |                             |
| parcels_centroids      | parcel_no             | Yes               |                             |
| neighborhoods          | neighborhood_id       | Yes               |                             |
| neighborhoods_centroids| id                    | Yes               |                             |
| subdivisions           | subdivision_id        | Yes               |                             |
| metro_lines            | id                    | Yes               |                             |
| bus_lines              | id                    | Yes               |                             |
| metro_stations         | station_code          | Yes               |                             |
| riyadh_bus_stations    | station_code          | Yes               |                             |
| qi_population_metrics  | grid_id               | Yes               |                             |
| qi_stripes             | strip_id              | Yes               |                             |

---

## Key Considerations
- **If a table contains only a single record per run:** Upsert is not meaningful; consider using replace mode.
- **If no unique key exists:** Upsert is not possible; use append or replace, and deduplicate in the pipeline if needed.
- **Composite keys:** If a table requires a composite key for uniqueness, ensure a unique constraint exists in the schema.
- **Schema drift:** If the source data changes, review and update the schema and uniqueness strategy accordingly.

---

## Action Items for Developer
- Review each table's schema and data characteristics.
- Confirm that the primary/unique key exists and is enforced in the database.
- For tables without a unique key, recommend the appropriate write mode (replace/append).
- For tables with a unique key, ensure upsert logic is used and tested.
- Document any exceptions or special cases. 