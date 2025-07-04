# Pipeline Table Uniqueness & Upsert Review

This document provides a comprehensive overview of all tables written to by the pipeline, their schemas, and the current state of unique/primary key constraints. It is intended for a developer unfamiliar with the project to make informed recommendations for upsert, replace, or append strategies for each table.

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