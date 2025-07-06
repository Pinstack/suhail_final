# Delta Enrichment TODO

This TODO list breaks down the implementation plan for the Delta Enrichment Pipeline, following the PRD and a strict Test-Driven Development (TDD) approach.

---

## Phase 1: Foundational Fixes & Core Logic (Sequential)

- [x] **P1-T1: [Test] Write Failing Test for Geometric Pipeline to Temp Table**
    - [x] Create `test_run_pipeline_with_save_as_temp...` test case.
    - [x] Ensure pipeline writes to a temp table and creates an index, without touching production tables.

- [x] **P1-T2: [Dev] Implement Geometric Pipeline to Temp Table**
    - [x] Modify `pipeline_orchestrator.py` to handle `save_as_temp` and create the required index.
    - [x] (Depends on P1-T1)

- [x] **P1-T3: [Test] Write Failing Test for Delta Detection SQL**
    - [x] Create test for SQL that finds parcels with new/changed transaction prices.
    - [x] Ensure test covers all change types: `new`, `null_to_positive`, `zero_to_positive`, `price_changed`.

- [x] **P1-T4: [Dev] Fix & Verify Delta Detection SQL**
    - [x] Debug the query in `strategies.py` until the test passes.
    - [x] (Depends on P1-T3)
    - [x] **For each parcel with a detected transaction data change, trigger all enrichment API calls (transaction, price metrics, building rules).**

- [x] **P1-T5: [Test] Write Failing Test for Delta Enrichment CLI**
    - [x] Test that `delta-enrich --auto-geometric` runs end-to-end, including temp table creation, delta detection, and enrichment.

- [x] **P1-T6: [Dev] Implement Delta Enrichment CLI Automation**
    - [x] Add `--auto-geometric` option to CLI.
    - [x] Automate temp table creation, delta detection, enrichment, and cleanup.
    - [ ] (Depends on P1-T5)

---

## Phase 2: Robustness, Error Handling, and Documentation

- [x] **P2-T1: [Test] Write Failing Test for Error Handling**
    - [x] Simulate missing temp table, DB errors, and ensure user-friendly errors (no raw tracebacks).

- [x] **P2-T2: [Dev] Implement Robust Error Handling**
    - [x] Add error handling to CLI and pipeline logic.
    - [ ] (Depends on P2-T1)

- [x] **P2-T4: [Dev] Add Monitoring Metrics**
    - [x] Log structured JSON metrics and run summaries after each `delta-enrich` run.

- [x] **P2-T3: [Docs] Update Documentation**
    - [x] Document delta enrichment workflow, CLI usage, and troubleshooting in `README.md` and internal docs.

---

## Phase 3: Performance, Monitoring, and Final QA

- [ ] **P3-T1: [Test] Write Performance Test**
    - [ ] Test delta enrichment on 1M+ parcels for runtime and memory usage.

- [ ] **P3-T2: [Dev] Optimize for Scale**
    - [ ] Profile and optimize SQL, batch size, and memory usage.
    - [ ] (Depends on P3-T1)

- [ ] **P3-T3: [Test] Final QA & Regression**
    - [ ] Run full regression suite and verify no data loss or duplication.

- [ ] **P3-T4: [Docs] Finalize Release Notes**
    - [ ] Summarize changes, usage, and migration steps for stakeholders.

---

## Success Criteria (from PRD)

- [ ] Delta detection SQL completes in <5 minutes for 1M parcels.
- [ ] End-to-end `delta-enrich --auto-geometric` is idempotent and robust.
- [ ] All CLI output is clear and actionable.
- [ ] >85% code coverage for new/modified modules.
- [ ] All temporary tables are cleaned up after runs (success or failure).
- [ ] No raw SQL tracebacks on user error.

---

**Reference:** See `docs/Delta_enrichment_PRD.md` for full requirements, acceptance criteria, and user stories. 
