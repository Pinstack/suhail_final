# Upsert Bottleneck Handoff: PostGIS Pipeline

## Overview

The pipeline now uses PostgreSQL's `INSERT ... ON CONFLICT DO UPDATE` (upsert) for idempotent, robust writes to spatial tables. However, the pipeline currently fails with:

```
psycopg2.errors.InvalidColumnReference: there is no unique or exclusion constraint matching the ON CONFLICT specification
```

This error occurs because the upsert logic requires a unique constraint or primary key on the column(s) specified in `ON CONFLICT`, but the target tables do **not** have the required constraints.

---

## 1. Upsert Key Table (Decision Matrix)

| Table Name           | Upsert Key Column | Is Unique in Data? | Is Unique/PK in Schema? | Notes/Exceptions |
|----------------------|-------------------|--------------------|------------------------|------------------|
| parcels              | parcel_id         | [FILL]             | [FILL]                 |                  |
| parcels_centroids    | parcel_no         | [FILL]             | [FILL]                 |                  |
| neighborhoods        | neighborhood_id   | [FILL]             | [FILL]                 |                  |
| ...                  | ...               | ...                | ...                    | ...              |

**Action:**
- For each table, confirm the upsert key column, check if it is unique in the data, and if it is defined as unique/PK in the schema.
- If not unique in data, upsert cannot be used on that column.
- If not unique/PK in schema, an Alembic migration is required.

---

## 2. Pipeline Upsert Logic Reference

- **Upsert Implementation:**
  - `src/meshic_pipeline/persistence/postgis_persister.py`:
    - `PostGISPersister.write` (public method)
    - `PostGISPersister._upsert` (private method)
  - Upsert is triggered when `id_column` is provided and `if_exists='append'`.
- **Orchestrator/Config:**
  - `src/meshic_pipeline/pipeline_orchestrator.py`:
    - Passes `id_column` from `settings.id_column_per_layer` to `persister.write` for each layer.
  - The mapping of layers to upsert key columns is defined in the pipeline settings/config.

---

## 3. Alembic Migration & Schema State

- **Check Alembic migrations for each table:**
  - Are there existing unique constraints or primary keys on the upsert key columns?
  - If not, you must create a migration to add them. Example:

```python
from alembic import op
op.create_unique_constraint(
    "uq_parcels_parcel_id",
    "parcels",
    ["parcel_id"]
)
```

- **Current Model Definitions:**
  - Review `src/meshic_pipeline/persistence/models.py` and any other relevant model files for table/column definitions.

---

## 4. Sample Data (Optional but Recommended)

Provide a small sample (5–10 rows) for each upserted table, showing the upsert key column and a few other columns. Example:

**parcels:**
| parcel_id | geometry | ... |
|-----------|----------|-----|
| 1010001   | ...      | ... |
| 1010002   | ...      | ... |

**parcels_centroids:**
| parcel_no | geometry | ... |
|-----------|----------|-----|
| 123/9     | ...      | ... |
| 477       | ...      | ... |

**neighborhoods:**
| neighborhood_id | geometry | ... |
|-----------------|----------|-----|
| 10100079        | ...      | ... |

---

## 5. Known Issues / Edge Cases

- Some tables may have nulls or duplicate values in the intended upsert key column. These must be resolved before upsert can be used.
- If a table cannot have a unique constraint on the intended column, upsert is not possible for that table.
- If the upsert key is a composite (multi-column) key, update the logic and migrations accordingly.

---

## 6. Next Steps / Action Items

1. **Audit Data:**
   - For each upserted table, confirm the upsert key column and check for uniqueness in the data.
2. **Check Schema:**
   - Confirm if the upsert key column is a unique constraint or primary key in the schema.
3. **Update Schema:**
   - If needed, create Alembic migrations to add unique constraints/PKs.
4. **Test Pipeline:**
   - Rerun the pipeline to confirm upsert works and no errors are raised.
5. **Document Decisions:**
   - Update this document with the final decisions and actions taken.

---

## 7. References
- [PostgreSQL ON CONFLICT documentation](https://www.postgresql.org/docs/current/sql-insert.html#SQL-ON-CONFLICT)
- [Alembic documentation](https://alembic.sqlalchemy.org/en/latest/)
- [GeoPandas to_postgis docs](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_postgis.html)

---

## 8. Contact / Handoff
- Last pipeline/DB state: [describe or link to logs]
- Last code commit: [commit hash or description]
- For questions, contact: [your name/email]

---

**Please fill in the missing fields and proceed with the action items above. This will ensure the upsert logic is robust, idempotent, and production-ready.** 