# Story 005: Delta Enrichment Productization

Epic: Delta Enrichment Productization
Type: Feature
Owner: Data Engineering
Status: Ready for Dev

## Goal
Standardize fresh-table lifecycle, change stats, and scheduling for delta enrichment.

## Tasks
- Ensure `--auto-geometric` creates and cleans up fresh table.
- Validate change categories and summary reporting.
- Add scheduling guidance to docs; sample cron entries.

## Acceptance Criteria
- Delta run produces summary with counts per change type.
- Fresh table is dropped on success; retained on failure with warning.

## Definition of Done
- Documentation updated; sample outputs included.
