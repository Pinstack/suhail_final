# Directory Index — `docs/`

Generated and curated reference for humans and LLMs. Descriptions reflect file purpose (not only filenames). Hidden files omitted. Sort: root files alphabetically, then subfolders.

## Project scan

- **[BMAD_PROJECT_SCAN.md](./BMAD_PROJECT_SCAN.md)** — Brownfield snapshot: stack, doc map, BMAD next steps.

## Distillates (LLM-optimized)

- **[docs-distillate/_index.md](./docs-distillate/_index.md)** — Manifest for dense bullet distillates of major docs.
- **[docs-distillate/_index-validation-report.md](./docs-distillate/_index-validation-report.md)** — Distillate round-trip validation report.
- **[REPO_HYGIENE.md](./REPO_HYGIENE.md)** — Aggressive cleanup playbook and single source of truth.
- **[docs-distillate/01-requirements-and-product.md](./docs-distillate/01-requirements-and-product.md)** — PRD, brief, delta PRD, acceptance themes (bullets).
- **[docs-distillate/02-architecture-and-data.md](./docs-distillate/02-architecture-and-data.md)** — Architecture, schema, production ground truth (bullets).
- **[docs-distillate/03-stories-ops-cli.md](./docs-distillate/03-stories-ops-cli.md)** — Stories STORY-001–008, CLI audit, ops runbooks (bullets).

## Root documentation files

- **[ACCEPTANCE_CRITERIA.md](./ACCEPTANCE_CRITERIA.md)** — Epic-level acceptance checks for indexes, monitoring, delta, quality, API, schema, docs.
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** — Lean system architecture: two-stage pipeline, modules, NFRs.
- **[BROWNFIELD_PROJECT_DOCUMENTATION.md](./BROWNFIELD_PROJECT_DOCUMENTATION.md)** — Ground-truth production analysis, counts, gaps vs memory-bank.
- **[brownfield-architecture.md](./brownfield-architecture.md)** — Brownfield architecture narrative and technical debt notes.
- **[CLEAN_SLATE_PROTOCOL.md](./CLEAN_SLATE_PROTOCOL.md)** — Destructive local Postgres/PostGIS reset procedure (dev only).
- **[CLI_COMMAND_AUDIT.md](./CLI_COMMAND_AUDIT.md)** — Inventory of Typer commands and documentation gaps.
- **[Delta_enrichment_PRD.md](./Delta_enrichment_PRD.md)** — Product requirements for delta enrichment and `delta-enrich` CLI.
- **[handoff_upsert_bottleneck.md](./handoff_upsert_bottleneck.md)** — Reference-data bottleneck analysis (municipalities/neighborhoods).
- **[pipeline_table_uniqueness_review.md](./pipeline_table_uniqueness_review.md)** — Upsert keys and table uniqueness review.
- **[PRD.md](./PRD.md)** — Main product requirements: Meshic geospatial pipeline.
- **[PROJECT_BRIEF.md](./PROJECT_BRIEF.md)** — Executive brief: goals, MVP, personas.
- **[province_wide_scraping_plan.md](./province_wide_scraping_plan.md)** — DB-driven province and national scrape rollout plan.
- **[technical-decisions-template.md](./technical-decisions-template.md)** — Template for recording ADRs or technical decisions.

## Subdirectories

### working/

Scratch lists (not contractual specs):

- **[working/README.md](./working/README.md)** — What belongs here.
- **[working/Delta_enrichment_todo.md](./working/Delta_enrichment_todo.md)** — Delta enrichment task list.
- **[working/TODO.md](./working/TODO.md)** — Project todo / backlog notes.

### archive/

- **[archive/README.md](./archive/README.md)** — What is archived and why.
- **[archive/legacy-root-md/](archive/legacy-root-md/)** — Former root-level analysis reports (DB architecture, performance, incidents).
- **[archive/generated-txt/](archive/generated-txt/)** — Captured test/linter/CLI outputs (regenerate from tooling).
- **[archive/memory-bank/](archive/memory-bank/)** — Legacy memory-bank notes.
- **[archive/comprehensive-results/](archive/comprehensive-results/)** — Ad hoc generated analyses.
- **[archive/WHAT_TO_DO_NEXT_PIPELINE_TABLES.md](./archive/WHAT_TO_DO_NEXT_PIPELINE_TABLES.md)** — Legacy pipeline tables action plan.

### ops/

- **[migrations.md](./ops/migrations.md)** — How to run Alembic upgrades/downgrades and index migration notes.
- **[index-migration-runbook.md](./ops/index-migration-runbook.md)** — Epic 1 index migration: apply, verify, links to perf reports.

### reports/

- **[perf-baseline-20251017-1152.md](./reports/perf-baseline-20251017-1152.md)** — Query performance baseline capture.
- **[perf-post-index-20251017-1154.md](./reports/perf-post-index-20251017-1154.md)** — Performance after index migration.
- **[reports/generated/README.md](./reports/generated/README.md)** — Where `generate_db_report.py` writes `database_report.md` (gitignored).

### stories/

- **[STORY-001-indexes-migration-validation.md](./stories/STORY-001-indexes-migration-validation.md)** — Critical indexes migration and validation.
- **[STORY-002-perf-baseline-and-post.md](./stories/STORY-002-perf-baseline-and-post.md)** — Baseline and post-index performance measurement.
- **[STORY-003-monitoring-cli-outputs.md](./stories/STORY-003-monitoring-cli-outputs.md)** — Enhance monitoring CLI outputs.
- **[STORY-004-stale-tile-reset-schedule.md](./stories/STORY-004-stale-tile-reset-schedule.md)** — Automate stale `in_progress` tile reset.
- **[STORY-005-delta-enrichment-productization.md](./stories/STORY-005-delta-enrichment-productization.md)** — Delta enrichment productization.
- **[STORY-006-data-quality-framework.md](./stories/STORY-006-data-quality-framework.md)** — Data quality reporting framework.
- **[STORY-007-api-design-skeleton.md](./stories/STORY-007-api-design-skeleton.md)** — API design document and skeleton service.
- **[STORY-008-docs-transition.md](./stories/STORY-008-docs-transition.md)** — README and docs alignment with BMAD artifacts.

### tech-specs/

- **[EPIC-001-performance-and-monitoring.md](./tech-specs/EPIC-001-performance-and-monitoring.md)** — Epic tech spec: indexes, monitoring, stale reset.
- **[delta-enrichment-contract.md](./tech-specs/delta-enrichment-contract.md)** — Draft contract for delta classification, CLI, cleanup (STORY-005).

## Related (repository root)

- **[../REPOSITORY_INDEX.md](../REPOSITORY_INDEX.md)** — Top-level map of the whole repo (code, data, agent config).
- **[archive/comprehensive-results/SAUDI_ARABIA_PROVINCE_DISCOVERY_REPORT.md](./archive/comprehensive-results/SAUDI_ARABIA_PROVINCE_DISCOVERY_REPORT.md)** — Province discovery report (generated analysis).
