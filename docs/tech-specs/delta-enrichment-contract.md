# Delta enrichment — implementation contract (draft)

**Status:** Draft — align with **`docs/Delta_enrichment_PRD.md`** and **`docs/PRD.md`** before heavy implementation.  
**Owner:** TBD

## Goal

Re-enrich **only** parcels whose **transaction-related signal** from fresh MVT differs from production `parcels`, to cut API cost and runtime.

## Fresh table

- Default name: `parcels_fresh_mvt` (configurable).
- Produced by geometric pipeline with **`--save-as-temp`** and/or **`--auto-geometric`** on `delta-enrich` (see PRD).

## Change classes (trigger full API bundle)

When a parcel is classified into one of these, run **transactions + price metrics + building rules** for that parcel:

| Class | Meaning (informal) |
|-------|---------------------|
| `new` | Parcel appears in fresh MVT with transaction signal not represented as in prod |
| `null_to_positive` | `transaction_price` went from null to positive |
| `zero_to_positive` | From zero to positive |
| `price_changed` | Positive price changed materially (exact SQL TBD) |

**Non-triggers:** Negative or zero stored values do not trigger enrichment per PRD themes (confirm in code comments when implementing).

## Cleanup

- If fresh table was created via **`--auto-geometric`**, drop it after **successful** delta run; on failure, retain and log path for inspection.

## CLI UX

- Structured summary: counts per change class, duration, rows examined.
- Errors: user-facing message + hint; no raw tracebacks to stdout for expected failures.
- Exit codes: document matrix (success, partial, config error, DB error) when implementing.

## Observability

- Log line or JSON blob per run: timestamp, duration, counts by class, fresh table name, success flag.

## Open (must close before “done”)

- Exact SQL for classification and edge cases (disappeared price, duplicate rows).
- Interaction with `parcels.enriched_at` and idempotent upserts.
- Load test on subset before national runs.
