# Story 004: Automate Stale Tile Reset Scheduling

Epic: Monitoring & Alerting
Type: Ops
Owner: Platform Engineering
Status: Ready for Dev

## Goal
Automatically reset stale `in_progress` tiles to maintain pipeline throughput.

## Tasks
- Create a scheduled task (cron/systemd) to call `TileURL.reset_stale_in_progress(..., stale_minutes=60)`.
- Log count of tiles reset; add alert if repeated resets exceed threshold.
- Document setup steps and rollback.

## Acceptance Criteria
- Scheduled job installed in staging and production.
- Logs show periodic resets when stale tiles exist.

## Definition of Done
- Runbook updated; monitoring CLI reflects improved queue health.
