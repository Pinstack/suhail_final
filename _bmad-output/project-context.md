---
project_name: suhail_final
user_name: Raedmund
date: "2026-03-20"
sections_completed:
  - technology_stack
  - critical_rules
---

# Project context for AI agents

Lean rules for implementing code in **meshic-pipeline**. Prefer existing patterns in `src/meshic_pipeline/`. Full narrative lives in `docs/` and `docs/docs-distillate/`.

## Technology stack and versions

- **Language:** Python 3.9+ (`pyproject.toml`); **CI uses Python 3.11** — match CI when running tests locally.
- **Package:** `meshic-pipeline` 0.1.0, `src` layout, entrypoints `meshic-pipeline` and `check_db`.
- **DB:** PostgreSQL + PostGIS; SQLAlchemy 2.x, GeoAlchemy2, Alembic; async via `asyncpg` where used.
- **Geo / ETL:** GeoPandas, Shapely, h3/h3pandas, `mapbox-vector-tile`, mercantile, aiohttp.
- **CLI / config:** Typer, Pydantic / pydantic-settings, YAML + `.env` for secrets.
- **Tests:** pytest, pytest-asyncio, markers `slow`, `real_data` (`pythonpath` includes `src`, `scripts`).

## Critical implementation rules

### Pipeline and data

- **Orchestration:** Tile work is **DB-driven** via `tile_urls`; use row locking / `SKIP LOCKED` patterns already in `persistence/models.py` — do not invent ad hoc global queues.
- **Stages:** Stage 1 geometry (MVT → PostGIS) then Stage 2 enrichment (Suhail APIs); keep boundaries clear; `temp_*` tables are **staging only** — never assume they persist.
- **Idempotency:** Upserts and conflict handling are required for reruns; enrichment updates `parcels.enriched_at` on success.
- **Scale:** Production row counts are **millions** of parcels and **tens of millions** of metrics — avoid O(n) Python loops over full tables; use SQL batching (chunk sizes ~5000 appear in docs).

### Code organization

- **Package root:** `src/meshic_pipeline/` — new modules follow existing folders: `persistence/`, `enrichment/`, `geometry/`, `decoder/`, `downloader/`, `discovery/`.
- **CLI:** New commands go through `cli.py` with Typer; keep help strings and safe defaults consistent with documented commands in `docs/CLI_COMMAND_AUDIT.md`.
- **Migrations:** Schema changes require Alembic revisions under `alembic/versions/`; do not hand-edit production without a migration.

### Quality and testing

- Run **`pytest`** before merge; respect `@pytest.mark.slow` and `@pytest.mark.real_data` — do not assume real DB/data in unit tests.
- Prefer **integration tests** for DB and API boundaries; keep unit tests fast and deterministic.

### Security and configuration

- **Secrets:** Load from environment / `.env`; **never commit credentials**. If touching DB URLs, use settings from `config.py` patterns.
- **Arabic / UTF-8:** Preserve encoding and column normalization conventions used in MVT decode and persistence paths.

### Documentation

- When changing user-visible CLI or schema, update **`README.md`** and the relevant **`docs/`** file; `docs/index.md` lists canonical docs.
- For conflicting numbers, **`BROWNFIELD_PROJECT_DOCUMENTATION.md`** trumps older memory-bank-scale figures.

### Don’t miss

- **Indexes:** Join and filter paths on `parcels`, `parcel_price_metrics`, and `transactions` rely on documented indexes — consider migration + `EXPLAIN` when adding hot queries.
- **Stale tiles:** Long-running workers must cooperate with `reset_stale_in_progress` semantics — do not leave tiles stuck `in_progress` without a recovery path.
- **`numpy<2`** is pinned in dependencies — do not upgrade numpy major without validating the stack.
