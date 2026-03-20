# Story 002: Capture Performance Baseline and Post-Index Metrics

Epic: Performance Index Rollout & Query Tuning
Type: Technical
Owner: Data Engineering
Status: Ready for Dev

## Goal
Quantify performance impact of indexes and validate target p95 latency.

## Tasks
- Select 3 representative queries (joins, filters, time-series reads).
- Capture baseline timings (p50/p95) under realistic load.
- After index rollout, capture post-change timings.
- Document results in `docs/reports/perf-baseline-<date>.md` and `perf-post-<date>.md`.

## Acceptance Criteria
- Baseline and post-change reports exist in docs.
- p95 latency meets target (< 500 ms) or remediation plan created.

## Definition of Done
- Reports reviewed and approved; linked from runbook.
