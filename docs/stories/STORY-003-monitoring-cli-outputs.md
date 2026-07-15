# Story 003: Enhance Monitoring CLI Outputs

Epic: Monitoring & Alerting
Type: Feature
Owner: Platform Engineering
Status: Ready for Dev

## Goal
Provide actionable status and recommendations via `suhail-pipeline monitor`.

## Tasks
- Ensure `monitor status` outputs: tile queue counts by status, oldest in_progress age, top errors.
- Ensure `monitor recommend` computes next best action with batch sizes.
- Ensure `monitor schedule-info` prints cadence guidance.
- Add structured log line with summary metrics per run.

## Acceptance Criteria
- All three subcommands present with described fields.
- Outputs validated against staging data; examples added to docs.

## Definition of Done
- CLI help updated; README references corrected.
