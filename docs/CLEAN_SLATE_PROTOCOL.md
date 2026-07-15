# Clean Slate Protocol for Spatial Projects

> **WARNING:** This protocol is **DESTRUCTIVE**. Only proceed if you are on a development machine and no critical data exists in any local PostgreSQL instance. All local PostgreSQL/PostGIS data, logs, and configurations will be permanently deleted.

---

## Phase 1: Environment Reset (Execute with Caution)

- [ ] **1. Add Safety Warning:** Confirm you are on a development machine and that no critical data exists in any local PostgreSQL instance. This process is destructive.
- [ ] **2. Stop PostgreSQL Services:** Halt any running instances to release file locks.
  ```sh
  brew services stop --all
  ```
- [ ] **3. Uninstall All PostgreSQL Versions:** Remove all Homebrew-managed PostgreSQL and PostGIS packages.
  ```sh
  brew uninstall postgresql postgresql@14 postgresql@15 postgis
  ```
- [ ] **4. Eradicate Data Directories:** Completely remove all old data, logs, and configuration files.
  - **For Apple Silicon Macs:**
    ```sh
    rm -rf /opt/homebrew/var/postgres*
    ```
  - **For Intel Macs:**
    ```sh
    rm -rf /usr/local/var/postgres*
    ```

---

## Phase 2: Clean Installation and Configuration

- [ ] **5. Install PostGIS and PostgreSQL:** Use the `postgis` formula, which will pull in the latest compatible `postgresql` as a dependency.
  ```sh
  # This will install the default PostgreSQL version
  brew install postgis
  # Or, to pin a version:
  # brew install postgresql@14
  # brew install postgis
  ```
- [ ] **6. Initialize the Database Cluster:** Create the data directory using a performance-friendly locale. (Adjust path for your version/architecture if needed).
  ```sh
  initdb --locale=C -E UTF-8 /opt/homebrew/var/postgresql@16
  ```
- [ ] **7. Start the PostgreSQL Service:**
  ```sh
  brew services start postgresql@16
  ```
- [ ] **8. Create the Project Database:** **Crucially, use `template0`** to ensure a pristine, extension-free starting point.
  ```sh
  createdb suhail -T template0
  ```
- [ ] **9. Enable PostGIS Extension:** Activate PostGIS within your newly created database.
  ```sh
  psql -d suhail -c "CREATE EXTENSION postgis;"
  ```

---

## Phase 3: Application and Migration Setup

- [ ] **10. Install uv** (see [Astral docs](https://docs.astral.sh/uv/getting-started/installation/)) if not already available.
- [ ] **11. Install Python dependencies from lockfile:** From the repo root:
  ```sh
  uv sync --all-groups
  ```
  This installs the editable package and all runtime + dev dependencies declared in `pyproject.toml` / `uv.lock` (including Alembic, SQLAlchemy, GeoAlchemy2, and the configured Postgres driver).
- [ ] **12. Configure Alembic:**
  - [ ] Initialize a new `alembic` directory: `alembic init alembic`
  - [ ] Set `sqlalchemy.url` in `alembic.ini` (ideally sourced from an environment variable).
  - [ ] Point to your SQLAlchemy models in `alembic/env.py` by importing your `Base` and setting `target_metadata = Base.metadata`.

---

## Phase 4: Schema Generation and Verification

- [ ] **13. Generate Initial Migration:** Let Alembic autogenerate the first schema revision.
  ```sh
  uv run alembic revision --autogenerate -m "Initial database schema"
  ```
- [ ] **14. Manually Inspect the Migration File:**
  - [ ] Add `import geoalchemy2` at the top if it's missing.
  - [ ] Verify that `Geometry` types are used correctly.
  - [ ] Confirm that spatial indexes are created with `op.create_spatial_index(...)`, not `op.create_index(...)`.
  - [ ] Check for any redundant or incorrect operations.
- [ ] **15. Apply the Migration:** Upgrade the database to the latest version.
  ```sh
  uv run alembic upgrade head
  ```
- [ ] **16. Verify the Schema in PSQL:**
  - [ ] Check for tables: `psql -d suhail -c "\dt"`
  - [ ] Inspect a spatial table's structure: `psql -d suhail -c "\d+ your_spatial_table"`
  - [ ] Confirm PostGIS tracking: `psql -d suhail -c "SELECT * FROM geometry_columns;"`
- [ ] **17. Run Application Tests:** Execute your project's test suite to confirm that the database connection, schema, and spatial queries work as expected.

---

**Reference DB URL:**
```
postgresql+psycopg2://raedmundjennings@localhost:5432/suhail
```

---

**Last updated:** [Update this date when you run the protocol]

---

# **Verification Checklist**
- [ ] PostgreSQL/PostGIS fully uninstalled and data directories deleted
- [ ] PostgreSQL and PostGIS reinstalled and initialized
- [ ] Database created from `template0`
- [ ] PostGIS extension enabled
- [ ] Python virtual environment created and activated
- [ ] Dependencies installed
- [ ] Alembic initialized and configured
- [ ] Initial migration generated and checked for issues
- [ ] Migration applied successfully
- [ ] Schema and spatial columns verified
- [ ] Application tests pass

---

**By following this protocol, you can guarantee a clean, reproducible, and robust spatial database setup for your project every time.** 