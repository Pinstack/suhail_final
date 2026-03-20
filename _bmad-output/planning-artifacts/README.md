# Planning artifacts (BMM)

Per **`_bmad/bmm/config.yaml`**, this folder is the configured **`planning_artifacts`** root for BMAD workflows.

## Canonical sources in this repo

Product and planning content already lives under **`docs/`** (not duplicated here by default):

| Kind | Path |
|------|------|
| PRD | [../../docs/PRD.md](../../docs/PRD.md) |
| Brief | [../../docs/PROJECT_BRIEF.md](../../docs/PROJECT_BRIEF.md) |
| Acceptance | [../../docs/ACCEPTANCE_CRITERIA.md](../../docs/ACCEPTANCE_CRITERIA.md) |
| Architecture (lean) | [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) |
| Ground truth / brownfield | [../../docs/BROWNFIELD_PROJECT_DOCUMENTATION.md](../../docs/BROWNFIELD_PROJECT_DOCUMENTATION.md) |
| Stories | [../../docs/stories/](../../docs/stories/) |
| Tech specs | [../../docs/tech-specs/](../../docs/tech-specs/) |
| Doc index | [../../docs/index.md](../../docs/index.md) |

## Next BMAD actions

1. **`bmad-bmm-check-implementation-readiness`** — align PRD, UX (if any), architecture, epics/stories.
2. **`bmad-bmm-sprint-planning`** — emit **`sprint-status`** under **`../implementation-artifacts/`**.

If you prefer BMAD-native filenames in this directory, run the create-PRD / create-epics workflows with output here, or add thin symlinks/copies from `docs/` after team agreement.
