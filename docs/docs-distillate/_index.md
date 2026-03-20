---
type: bmad-distillate
sources:
  - "../PRD.md"
  - "../PROJECT_BRIEF.md"
  - "../Delta_enrichment_PRD.md"
  - "../ACCEPTANCE_CRITERIA.md"
  - "../ARCHITECTURE.md"
  - "../brownfield-architecture.md"
  - "../BROWNFIELD_PROJECT_DOCUMENTATION.md"
  - "../stories/"
  - "../CLI_COMMAND_AUDIT.md"
  - "../province_wide_scraping_plan.md"
  - "../ops/migrations.md"
  - "../handoff_upsert_bottleneck.md"
  - "../pipeline_table_uniqueness_review.md"
  - "../CLEAN_SLATE_PROTOCOL.md"
  - "../tech-specs/EPIC-001-performance-and-monitoring.md"
downstream_consumer: general
created: "2026-03-20"
token_estimate: 8064
parts: 3
---

# Docs distillate (index)

- Dense bullet distillates derived from primary `docs/` sources; split into three section files for LLM loading.
- Not included in section files (read originals): `docs/working/TODO.md`, `docs/working/Delta_enrichment_todo.md`, `technical-decisions-template.md`, `docs/reports/*`, most of `docs/archive/*` — still listed in `docs/index.md`.
- For ground truth on row counts and DB name, prefer `BROWNFIELD_PROJECT_DOCUMENTATION.md` over older memory-bank-scale figures.

## Validation

- [_index-validation-report.md](./_index-validation-report.md) — Round-trip style check (2026-03-20): **PASS_WITH_WARNINGS**; reconstructions under [_validation/](./_validation/).

## Section manifest

- [01-requirements-and-product.md](./01-requirements-and-product.md) — PRD, brief, delta PRD, acceptance themes.
- [02-architecture-and-data.md](./02-architecture-and-data.md) — architecture, brownfield architecture, ground-truth system state.
- [03-stories-ops-cli.md](./03-stories-ops-cli.md) — STORY-001–008, CLI audit, province plan, migrations, handoff, uniqueness, clean-slate, EPIC-001.
