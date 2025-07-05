# Delta Enrichment PRD
## 1. Executive Summary
- Re-engineer delta enrichment to process **only parcels with meaningful data changes** (e.g., new transaction prices).
- Compare fresh MVT tile transaction data to production DB data to reduce API costs, runtime, and data latency.
- **If and only if a parcel's transaction data has changed, the pipeline will call all enrichment APIs (transaction, price metrics, building rules) for that parcel.**
- Strict TDD and robust error handling required.

## 2. The Problem
- Current enrichment re-processes unchanged data, causing:
  - Financial waste (unnecessary API calls)
  - Long runtimes and compute waste
  - Data latency (slow to surface new changes)

## 3. Vision & Goals
- **Reduce costs** by 80%+ (API, compute)
- **Data freshness:** <24h for new transactions
- **Automate:** One CLI command for full delta workflow
- **Reliability:** Idempotent, robust, clear errors

## 4. Scope (In/Out)
- **In:**
  - TDD for all new logic
  - `--save-as-temp` in geometric pipeline
  - SQL-based delta detection
  - Automated `delta-enrich` CLI
  - State cleanup, temp table indexing
  - User-friendly errors, logging, docs
- **Out:**
  - GUI, advanced query optimization, upstream MVT changes

## 5. Key Functional Requirements
- **FR1:** Geometric pipeline can write parcels to a temp table (with index)
- **FR2:** Delta detection SQL finds all change types (`new`, `null_to_positive`, `zero_to_positive`, `price_changed`). **For each parcel with a detected transaction data change, trigger all enrichment API calls.**
- **FR3:** `delta-enrich` CLI automates the workflow, supports `--auto-geometric`
- **FR4:** Guaranteed cleanup of temp tables (even on failure)
- **FR5:** Actionable, user-friendly error messages (no raw tracebacks)