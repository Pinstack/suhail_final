---
type: distillate-validation
distillate: docs/docs-distillate/_index.md
sources:
  - docs/PRD.md
  - docs/PROJECT_BRIEF.md
  - docs/Delta_enrichment_PRD.md
  - docs/ACCEPTANCE_CRITERIA.md
  - docs/ARCHITECTURE.md
  - docs/brownfield-architecture.md
  - docs/BROWNFIELD_PROJECT_DOCUMENTATION.md
  - docs/stories/
  - docs/CLI_COMMAND_AUDIT.md
  - docs/province_wide_scraping_plan.md
  - docs/ops/migrations.md
  - docs/handoff_upsert_bottleneck.md
  - docs/pipeline_table_uniqueness_review.md
  - docs/CLEAN_SLATE_PROTOCOL.md
  - docs/tech-specs/EPIC-001-performance-and-monitoring.md
created: "2026-03-20"
---

## Validation summary

- Status: **PASS_WITH_WARNINGS**
- Method: Round-trip style — reconstructions produced **from distillate files only** (see `_validation/reconstruction-*.md`), then compared to primary sources by the validator.
- Information preserved (representative sample): **high** for requirements, architecture themes, table names, scale figures, CLI command names, story IDs, and epic/index acceptance themes.
- Gaps found: **low count** for PRD/ARCH bundles; **expected larger** for sources not individually reconstructed (full `stories/` folder, each ops doc line-by-line).
- Hallucinations detected in reconstructions: **none required** — reconstructions stay tied to distillate bullets; prose expansion is conservative.

## Gaps (information in originals with weak or no distillate bullet)

- **Per-story narrative and DoD detail:** `docs/stories/STORY-*.md` body text is folded into theme bullets in `03-stories-ops-cli.md`; edge acceptance notes and formatting from each story file are not losslessly encoded.
- **Line-level ops prose:** `docs/ops/migrations.md`, `province_wide_scraping_plan.md`, and `CLI_COMMAND_AUDIT.md` tables/examples: distillate keeps command names and recommendations, not every example block.
- **BROWNFIELD_PROJECT_DOCUMENTATION.md:** Long sections (e.g. extended code excerpts, full table attribute lists) are compressed; **counts and DB name `meshic`** are present; some secondary tables and narrative asides may be absent from bullets.
- **EPIC-001** risk tables and long checklist prose: captured as index/monitoring/stale-reset bullets; not every risk row is duplicated.
- **Reconstructor self-markers:** `reconstruction-PRD-bundle.md` flags **[POSSIBLE GAP]** for full SQL specs, exit-code matrix, and complete CLI error catalog — these are thin or absent in sources too; treat as “distillate correctly reflects source depth.”

## Hallucinations (reconstruction not traceable to distillate)

- None flagged in review; reconstructed claims map to distillate bullets.

## Possible gap markers (from reconstructor)

- Count reported by reconstructor agent: **14** (mostly “expected more detail” class for SQL, error catalogs, reconciliation procedures, and story-level nuance).
- See `_validation/reconstruction-PRD-bundle.md` and `_validation/reconstruction-ARCH-bundle.md` inline **[POSSIBLE GAP]** markers.

## Spot checks (original vs distillate)

| Theme | Original anchor | Distillate coverage |
|--------|-----------------|---------------------|
| PRD Stage 1–2 + delta | `docs/PRD.md` §Requirements | `01-requirements-and-product.md` — aligned |
| Monitoring FR | `docs/PRD.md` §4 | `01` acceptance + `03` EPIC-001/stories — aligned |
| Scale 2.16M / 76M metrics | PRD context + brownfield | `01` + `02` — aligned |
| DB name `meshic` | BROWNFIELD doc | `02` — aligned |
| STORY-001–008 IDs | stories | `03` — aligned |

## Recommendation

- Use **distillate + `_index.md`** for LLM context and navigation; open **original markdown** when editing a specific story, migration runbook, or brownfield appendix.
- Re-run validation after major edits to `docs/PRD.md` or `BROWNFIELD_PROJECT_DOCUMENTATION.md`.

## Artifacts

- Reconstructions (distillate-only input): `_validation/reconstruction-PRD-bundle.md`, `_validation/reconstruction-ARCH-bundle.md`
