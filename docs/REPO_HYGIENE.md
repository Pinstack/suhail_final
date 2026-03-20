# Repository hygiene — aggressive cleanup playbook

Prioritized for **disk win** and **git index sanity**. Derived from a 2026-03-20 tree audit.

## Single source of truth

| Concern | Canonical path | Do not duplicate |
|--------|----------------|------------------|
| BMAD Cursor/agent **skills** | `.agents/skills/` | Removed from repo: `.cursor/skills`, `.claude/skills`, `.agent/skills` |
| BMAD **workflows / installer** | `_bmad/` | Different role than `.agents/skills`; keep unless abandoning BMAD |
| Human docs | `docs/` | `docs/index.md` |
| LLM-dense doc bundle | `docs/docs-distillate/` | Run `_index-validation-report.md` after big doc edits |
| Agent implementation rules | `_bmad-output/project-context.md` | Regenerate when stack/conventions change |

## Done in this hygiene pass

- Removed **symlink skill trees** and empty `.cursor/`, `.claude/`, `.agent/` directories.
- **`git rm`** tracked junk: `.cursor/rules` (missing on disk), `src/meshic_pipeline/.DS_Store`, `logs/*.pid`.
- **`.gitignore`:** `logs/*.pid` (plus existing `.DS_Store`, `.venv_py39_backup/`).

## Recommended next steps (highest impact first)

1. **Delete local churn (not always in git):** `pipeline.log` (often ~100MB+), large `logs/*.log`, `.venv_py39_backup/` if unused (~200MB+).
2. **Policy for `.agents/skills/`:** Either **commit** as the canonical bundle or **`.gitignore`** and document install from BMAD — avoid a permanent “untracked mega-tree” without docs.
3. **Root report / test output files:** Done — former root `*_REPORT.md`, `*_test_results.txt`, and linter dumps live under **`docs/archive/legacy-root-md/`** and **`docs/archive/generated-txt/`**. Regenerate from CI when needed; do not move back to repo root.
4. **Lockfile strategy:** CI uses **uv**; reconcile `poetry.lock` vs `uv.lock` / `requirements.txt` so one path is authoritative.
5. **Large local data:** `retail_parcels.csv` (~25MB) — add `/retail_parcels.csv` to `.gitignore` if it must never be committed, or move under `data_raw/` with ignore rules.
6. **`alembic/versions_backup/`:** Keep, archive to docs, or delete only after confirming no operational dependency.

## Security

- `.env` should remain **untracked**. If it was ever pushed, **rotate credentials** and consider history scrubbing.

## Distillate validation

- After substantive edits to sources listed in `docs/docs-distillate/_index.md` frontmatter, re-run validation: reproduce reconstructions from distillate-only, compare to sources, update `_index-validation-report.md`.
