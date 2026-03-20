# Repository index — `suhail_final`

High-level map of the whole tree for navigation and onboarding. Pair with [docs/index.md](./docs/index.md) for documentation detail and [docs/docs-distillate/_index.md](./docs/docs-distillate/_index.md) for LLM-dense context.

## Application code

| Path | Role |
|------|------|
| [src/meshic_pipeline/](src/meshic_pipeline/) | Installable package: CLI (`cli.py`), geometric/enrichment runners, persistence, enrichment, geometry, decoder, discovery. |
| [alembic/](alembic/) | Database migrations (`env.py`, `versions/`, `versions_backup/`). |
| [tests/](tests/) | `pytest` suites: `unit/`, `integration/`. |
| [scripts/](scripts/) | Operational and utility scripts (`util/`, `db/`, reports). |

## Configuration and tooling

| Path | Role |
|------|------|
| [pyproject.toml](pyproject.toml) | Project `meshic-pipeline`, dependencies, `[project.scripts]`, pytest config, `[dependency-groups].dev`. |
| [uv.lock](uv.lock) | Locked dependency graph for reproducible installs (`uv sync --frozen`). |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | CI: `astral-sh/setup-uv`, `uv sync --all-groups --frozen`, `uv run pytest`. |

## Documentation and BMAD

| Path | Role |
|------|------|
| [docs/](docs/) | PRD, architecture, stories, acceptance criteria, ops; see [docs/index.md](docs/index.md). |
| [docs/BMAD_PROJECT_SCAN.md](docs/BMAD_PROJECT_SCAN.md) | Snapshot scan: stack, scale, artifact locations (2026-03-20). |
| [_bmad/](_bmad/) | BMAD module config and workflows (installer-managed). |
| [_bmad-output/](_bmad-output/) | BMAD-generated artifacts (`project-context.md`, planning/implementation placeholders). |

## Agent / IDE skill bundles

| Path | Role |
|------|------|
| [.agents/skills/](.agents/skills/) | **Canonical** BMAD skill packages for agents (54). No `.cursor/`, `.claude/`, or `.agent/` skill trees in-repo — configure your IDE to load from here or copy as needed. |
| [_bmad/](_bmad/) | BMAD installer workflows and core tasks (distinct from Cursor `SKILL.md` bundles). |

## Data, caches, and local artifacts (often gitignored)

| Path | Role |
|------|------|
| [data_raw/](data_raw/) | Raw input data (if present). |
| [sample_data/](sample_data/) | Sample inputs for tests or demos. |
| [tiles_cache/](tiles_cache/), [temp_tiles/](temp_tiles/), [stitched/](stitched/) | Tile and stitch caches (see `.gitignore`). |
| [logs/](logs/) | Local log output from pipelines/watchers. |
| [exports/](exports/) | Export outputs. |
| [docs/archive/comprehensive-results/](docs/archive/comprehensive-results/) | Archived generated analyses (e.g. province discovery). |
| [.venv/](.venv/), [.venv_py39_backup/](.venv_py39_backup/) | Local virtualenvs (backup dir should stay local-only). |

## Other roots

| Path | Role |
|------|------|
| [README.md](README.md) | Product overview, quick start, CLI summary. |
| [docs/archive/memory-bank/](docs/archive/memory-bank/) | Legacy memory-bank notes (historical; prefer `docs/` + distillates). |
| [assets/](assets/) | Static assets if any. |

## Entrypoints (from `pyproject.toml`)

- `meshic-pipeline` → `meshic_pipeline.cli:app`
- `check_db` → `meshic_pipeline.utils.db_checker:app`
