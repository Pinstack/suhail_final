# Story 006: Data Quality Framework (Phase 1)

Epic: Data Quality Framework
Type: Feature
Owner: Data Analytics
Status: Ready for Dev

## Goal
Establish baseline completeness and validity metrics, and publish a data quality report.

## Tasks
- Compute completeness: % parcels with `neighborhood_id`, `province_id`, `enriched_at`.
- Define outlier thresholds for `price_of_meter`, `transaction_price`; flag counts.
- Generate report to `docs/reports/data-quality-<date>.md`.

## Acceptance Criteria
- Report includes completeness and outlier summaries by province.
- Thresholds documented; false positives reviewed.

## Definition of Done
- Report committed; linked in README/PRD.
