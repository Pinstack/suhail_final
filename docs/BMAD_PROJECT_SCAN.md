# BMAD project scan — suhail_final

**Date:** 2026-03-20  
**Owner:** Raedmund (from `_bmad/bmm/config.yaml`)  
**Purpose:** Brownfield snapshot after documentation indexing and distillate generation — not a full interactive `document-project` state machine.

## Classification

- **Type:** Python data platform — geospatial ETL + API enrichment (PostGIS, MVT, Typer CLI).
- **Maturity:** Production-scale dataset documented in `BROWNFIELD_PROJECT_DOCUMENTATION.md` (millions of parcels and metrics).
- **Package:** `suhail-pipeline` (`pyproject.toml`), source layout under `src/suhail_pipeline/`.

## Authoritative documentation

| Artifact | Path |
|----------|------|
| Doc index | [index.md](./index.md) |
| Repo-wide index | [../REPOSITORY_INDEX.md](../REPOSITORY_INDEX.md) |
| LLM distillate manifest | [docs-distillate/_index.md](./docs-distillate/_index.md) |
| Agent rules | [_bmad-output/project-context.md](../_bmad-output/project-context.md) |
| Ground truth vs legacy claims | [BROWNFIELD_PROJECT_DOCUMENTATION.md](./BROWNFIELD_PROJECT_DOCUMENTATION.md) |

## Gaps addressed in this pass

- Added `docs/index.md` and root `REPOSITORY_INDEX.md`.
- Added `docs/docs-distillate/` (three section files + `_index.md`) derived from primary docs via structured extraction.
- Wrote `_bmad-output/project-context.md` for implementation agents.
- Skill trees: **single canonical** `.agents/skills/` — duplicate `.cursor`/`.claude`/`.agent` skill paths removed from the repo (see `docs/REPO_HYGIENE.md`).
- Distillate **validation report** and distillate-only **reconstructions** under `docs/docs-distillate/_validation/`.
- Legacy root reports, generated text dumps, and **memory-bank** consolidated under **`docs/archive/`**; working scratch lists under **`docs/working/`** (see `docs/archive/README.md`).

## Recommended next BMAD steps

1. Run `bmad-bmm-check-implementation-readiness` when PRD/UX/architecture/epics are aligned in `_bmad-output` paths, or confirm `docs/` equivalents.
2. Run `bmad-bmm-sprint-planning` to materialize `sprint-status` under `_bmad-output/implementation-artifacts/`.
3. If `.env` was ever committed, rotate credentials after `git rm --cached .env`.

## Scan notes

- `_bmad-output/planning-artifacts` and `implementation-artifacts` were empty placeholders before this pass; `project-context.md` now populated.
- CI uses Python **3.11**; `requires-python` allows **3.9+** — prefer 3.11 for parity with CI when developing.
