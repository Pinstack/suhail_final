# Meshic Geospatial Pipeline Implementation Plan

## 🚦 **Next Actions Summary (as of Baseline Validation Phase)**

| Step | Action | Status |
|------|--------|--------|
| 1    | Complete environment setup | ✅ Complete |
| 2    | Run 3x3 Riyadh baseline test | ✅ Complete (with error) |
| 3    | Run enrichment pipeline test | ✅ Complete |
| 4    | Update memory bank & documentation | ⬜️ Pending |
| 5    | Expand and run test suite | ✅ Complete |
| 6    | Prepare for multi-province validation | ⬜️ Pending |
| 7    | Plan for scaling/future phases | ⬜️ Pending |
| 8    | Maintain documentation & best practices | ⬜️ Ongoing |

---

# Meshic Geospatial Pipeline Implementation Plan

This document outlines the implementation plan for the Meshic Geospatial Data Pipeline following database reset and memory bank cleanup. All tasks are organized around our git workflow and systematic validation approach.

## 🎯 **Current Project Status**

### **Foundation State: Clean Baseline Established**
- **Database**: Fresh PostGIS schema (recently reset) with robust spatial design
- **Architecture**: Proven async pipeline components ready for testing
- **Git Status**: Clean baseline with `v0.1.0-baseline` tag created
- **Data State**: Empty database ready for baseline validation
- **Scope**: Commercial data capture for client sales (not Suhail platform development)

### **Business Context**
- **Objective**: Extract Saudi real estate data to build commercial analytics products
- **Target Market**: Client sales and analytics services
- **Data Source**: Suhail.ai MVT tiles and enrichment APIs
- **Scale Goal**: All 6 Saudi provinces (estimated 6M+ parcels based on Riyadh testing)

## 📋 **Phase 1: Baseline Validation & Testing**

### **1.1 Git Workflow Setup** ✅ **COMPLETED**
- ✅ **Feature Branch**: `feat/database-reset-baseline` created and merged
- ✅ **Baseline Tag**: `v0.1.0-baseline` established
- ✅ **Testing Branch**: `test/3x3-riyadh-baseline` ready for validation
- ✅ **Cleanup**: All outdated files removed (27 files, 5,756 deletions)

### **1.2 3x3 Riyadh Baseline Test** ✅ **COMPLETED**
**Priority**: HIGH - Validate basic pipeline with fresh database

**Scope**: 
- **Grid**: 3x3 tiles (9 tiles total) in central Riyadh
- **Expected Parcels**: ~1,000-2,000 parcels for initial validation
- **Purpose**: Confirm pipeline + database integration works

**Tasks**:
- [x] **Source Environment**: Activate `.venv` before running commands
- [x] **Run Geometric Pipeline**: `meshic-pipeline geometric` (or `python -m meshic_pipeline.cli geometric`)
- [x] **Verify Database Population**: Check parcels, neighborhoods, subdivisions tables
- [x] **Validate Schema**: Confirm data types and foreign key relationships
- [ ] **Performance Check**: Measure processing time and memory usage

**Results:**
- Parcels table and reference tables populated with spatial data
- Foreign key relationships working
- No pipeline errors or data corruption
- Geometry column registration and type casting issues resolved
- Pipeline now runs successfully for all layers

**Git Strategy**:
```bash
# If successful
git add .
git commit -m "test: validate 3x3 baseline with fresh database

- Process 9 tiles successfully in central Riyadh
- Populate {X} parcels with complete spatial data
- Verify foreign key relationships working
- Confirm schema robustness with real data"

# Create success tag
git tag v0.1.1-3x3-validated
```

### **1.2a Post-Baseline Test Plan** 🧪 **(To be executed after 3x3 grid validation)**

**Objective:** Ensure pipeline correctness, data integrity, and prevent regressions after establishing a working baseline.

**Test Types & Priorities:**
- **Unit Tests:**
  - Test isolated utility functions (e.g., tile decoding, geometry processing, API client logic).
  - Focus on edge cases and error handling.
- **Integration Tests:**
  - Validate end-to-end pipeline stages (tile download → decode → DB insert → enrichment).
  - Use test DB or fixtures to ensure data flows correctly.
- **Data Validation Tests:**
  - Check referential integrity (foreign keys, type safety).
  - Validate spatial data accuracy and schema alignment.
  - Confirm proper handling of Arabic text and Unicode.
- **Regression Tests:**
  - Lock in working behaviors from the 3x3 test to catch future breakage.
  - Add tests for any bugs or issues discovered during baseline validation.
- **Performance/Resource Tests:**
  - Monitor memory usage and processing time for small batches.
  - Ensure no memory leaks or excessive resource consumption.

**Rationale:**
- Tests written after the 3x3 grid run will reflect real data, observed edge cases, and a stable baseline.
- This approach ensures tests are meaningful, actionable, and less likely to require major rewrites.

**Next Steps:**
- [ ] Document any issues or edge cases found during 3x3 test
- [ ] Write and run tests as outlined above
- [ ] Integrate tests into CI/CD workflow if applicable

### **1.3 Enrichment Pipeline Test** 🔄 **NEXT**
**Priority**: HIGH - Validate API integration with baseline data

**Prerequisites**: 3x3 baseline test completed successfully

**Tasks**:
- [ ] **Test Fast Enrichment**: `meshic-pipeline fast-enrich --limit 100`
- [ ] **Monitor Success Rate**: Track enrichment coverage percentage
- [ ] **Verify API Integration**: Check all 3 API endpoints working
- [ ] **Data Quality Check**: Ensure no garbage data in enrichment tables
- [ ] **Performance Metrics**: Measure batch processing efficiency

**Expected Results**:
- High enrichment success rate (95%+ expected)
- All 3 API endpoints (transactions, building rules, price metrics) working
- Arabic text properly stored and retrieved
- No API timeout or data corruption issues

## 📋 **Phase 2: Multi-Province Validation**

### **2.1 Second Province Test** 🔄 **UPCOMING**
**Priority**: HIGH - Validate database handles multiple provinces

**Recommended Province**: Eastern or Riyadh (different from 3x3 test area)

**Purpose**: 
- Confirm database schema handles multiple provinces safely
- Test province-specific tile servers
- Validate no data conflicts or overwriting

**Tasks**:
- [ ] **Select Test Province**: Choose Eastern or Riyadh for validation
- [ ] **Small Grid Test**: Start with small area (3x3 or 5x5 grid)
- [ ] **Run Province Pipeline**: Use province-specific configuration
- [ ] **Verify Data Separation**: Confirm no conflicts with baseline data
- [ ] **Test Enrichment**: Validate enrichment works with multi-province data

**Git Strategy**:
```bash
git checkout -b test/multi-province-validation
# After successful test
git commit -m "test: validate multi-province database handling

- Successfully process second province without conflicts
- Confirm schema supports multiple geographic regions
- Verify province-specific tile servers working
- Validate enrichment pipeline with diverse data"
```

### **2.2 Full Province Scale Test** 🔄 **FUTURE**
**Priority**: MEDIUM - Validate architecture at production scale

**Scope**: Complete province (based on 52x52 Riyadh testing = 1M+ parcels)

**Purpose**:
- Test database performance at scale
- Validate chunked processing efficiency
- Confirm memory management and error handling
- Prepare for full Saudi Arabia rollout

## 📋 **Phase 3: Full Saudi Arabia Rollout**

### **3.1 All 6 Provinces Processing** 🔄 **FUTURE**
**Priority**: MEDIUM - Complete data capture coverage

**Provinces**: Riyadh, Eastern, Madinah, Makkah, Al_Qassim, Asir

**Strategy**:
- Process provinces sequentially to monitor performance
- Use efficient chunked processing patterns
- Monitor database growth and performance
- Track enrichment success rates across provinces

### **3.2 Dynamic Boundary Discovery Development** 🔄 **FUTURE**
**Priority**: LOW - Automation enhancement

**Objective**: Build system to automatically discover province extents

**Approach**:
- Use lower zoom levels to identify admin boundaries
- Extract bbox coordinates dynamically
- Generate z15 tile lists automatically
- Eliminate manual coordinate management

## 📋 **Current Development Commands**

### **Package Installation & Setup**
```bash
# Install package in development mode
uv add -e .

# Activate virtual environment
source .venv/bin/activate  # or appropriate activation for your shell

# Verify installation
meshic-pipeline --help
```

### **Testing Commands**
```bash
# Basic geometric pipeline (3x3 grid)
meshic-pipeline geometric

# Alternative if package not in PATH
python -m meshic_pipeline.cli geometric

# Enrichment testing
meshic-pipeline fast-enrich --limit 100

# Monitor pipeline status
meshic-pipeline monitor status

# Database validation
python scripts/check_db.py
```

### **Git Workflow Commands**
```bash
# Create feature branch for new work
git checkout -b feat/description-of-work

# Commit following conventions
git commit -m "feat: description of new feature"
git commit -m "test: validation of functionality"
git commit -m "fix: correction of issue"

# Create tags for milestones
git tag v0.1.X-milestone-name

# Push with tags
git push origin main --tags
```

## 📊 **Success Metrics & Validation**

### **Phase 1 Success Criteria**
- [ ] 3x3 grid processes without errors
- [ ] Database populated with expected table structure
- [ ] Foreign key relationships functional
- [ ] Enrichment pipeline operational with reasonable success rate
- [ ] No memory leaks or performance issues

### **Phase 2 Success Criteria**
- [ ] Multiple provinces stored without conflicts
- [ ] Database performance remains acceptable
- [ ] Province-specific configurations working
- [ ] Enrichment scales across different geographic regions

### **Phase 3 Success Criteria**
- [ ] All 6 Saudi provinces successfully processed
- [ ] Database handles full scale (6M+ parcels estimated)
- [ ] Performance optimized for production use
- [ ] Commercial data product ready for client delivery

## 🚨 **Critical Reminders**

### **Database Interaction Rules**
- **NEVER** interact with database directly - always use Alembic for schema changes
- **ALWAYS** use `uv` for dependency management
- **ALWAYS** source `.venv` before running Python commands
- **Database is source of truth** - all documentation must align with actual schema

### **Git Workflow Rules**
- Follow established commit conventions (feat/fix/test/docs)
- Create feature branches for significant work
- Tag major milestones for easy reference
- Keep main branch clean and deployable

### **Development Priorities**
1. **Validate Current Architecture**: Ensure 3x3 baseline works perfectly
2. **Test Multi-Province Capability**: Confirm database design is robust
3. **Scale Systematically**: Don't skip validation steps
4. **Maintain Commercial Focus**: Remember this is for client products, not platform development

This TODO reflects the actual current state: fresh database, proven architecture, and systematic validation approach to reach full Saudi Arabia coverage for commercial data products.

## 📘 **Comprehensive Unit Testing Plan**

### 1. Objectives
- Ensure correctness of all core utility functions and logic in isolation.
- Catch edge cases and regressions early, before integration or pipeline runs.
- Validate error handling, data validation, and type safety.
- Provide a foundation for robust integration and regression testing.

### 2. Scope of Unit Testing

#### A. Tile Discovery & Download
- **Functions**: Tile list generation, tile server URL construction, bounding box calculations.
- **Tests**:
  - Correct tile list for given bbox/zoom.
  - URL formatting for all provinces.
  - Edge cases such as bboxes on province boundaries and invalid input values.

#### B. MVT Decoding & Geometry Processing
- **Functions**: MVT tile decoding, geometry validation, CRS transformation, geometry stitching.
- **Tests**:
  - Decoding valid and invalid MVT tiles.
  - Geometry type checks (multipolygon, no self-intersections).
  - CRS conversion accuracy.
  - Handling of empty or malformed tiles.

#### C. Database Utility Functions
- **Functions**: Chunked inserts, upsert key generation, type casting, reference lookups.
- **Tests**:
  - Chunking logic for various batch sizes.
  - Upsert key uniqueness and error handling.
  - Type casting for all supported DB types.
  - Reference table lookups such as province or municipality by name.

#### D. Enrichment API Client
- **Functions**: API request construction, response parsing, error handling, retry logic.
- **Tests**:
  - Correct API URL and payload for all endpoints.
  - Parsing of valid and invalid API responses.
  - Retry logic on timeouts or 5xx errors.
  - Handling of missing or malformed data in API responses.

#### E. Data Validation Utilities
- **Functions**: Schema validation, foreign key checks, Arabic text handling, Unicode normalization.
- **Tests**:
  - Validation of all expected schema fields.
  - Foreign key relationship checks (mocked DB).
  - Correct storage and retrieval of Arabic or other Unicode text.
  - Handling of missing or malformed fields.

#### F. Configuration & Environment
- **Functions**: Config file parsing, environment variable overrides, validation logic.
- **Tests**:
  - Parsing of valid and invalid YAML configuration files.
  - Environment variable override precedence.
  - Validation of required config fields and types.

#### G. Logging & Error Handling
- **Functions**: Structured logging, exception wrapping, error message formatting.
- **Tests**:
  - Logging output for success and failure cases.
  - Exception propagation and custom error messages.
  - Handling of partial failures, such as a batch with some errors.

### 3. Test Organization
- **Location**: Place unit tests in `tests/unit/` or `scripts/tests/` as appropriate.
- **Framework**: Use `pytest` for async and DB-related tests.
- **Mocking**: Utilize `unittest.mock` or `pytest-asyncio` to mock external dependencies.
- **Mocked Dependencies**: External APIs, DB connections, and file I/O should be mocked.

### 4. Coverage Checklist
| Area                   | Example Test Cases |
|------------------------|-------------------|
| Tile Discovery         | Generates correct tile list, handles edge bboxes, invalid input |
| MVT Decoding           | Decodes valid/invalid tiles, geometry type, CRS conversion, empty tiles |
| Geometry Processing    | Stitching, validation, error on invalid geometry |
| DB Utilities           | Chunking, upsert key, type casting, reference lookup |
| API Client             | URL/payload, response parsing, retry logic, error handling |
| Data Validation        | Schema fields, FK checks, Arabic/Unicode, missing fields |
| Config Parsing         | Valid/invalid YAML, env overrides, required fields |
| Logging/Error Handling | Log output, exception propagation, partial failure handling |

### 5. Example Test Skeletons
Provide minimal pytest examples for each module to guide future implementations.

### 6. Best Practices
- Test all edge cases: empty input, invalid data, and boundary conditions.
- Isolate units: mock dependencies such as the DB, APIs, and file I/O.
- Use fixtures for common test data and setup/teardown.
- Automate test execution in CI/CD workflows.
- Document each test with clear coverage goals and rationale.

### 7. Next Steps
- Set up the test directory structure if not already present.
- Identify core utility modules and functions for each area above.
- Write initial test skeletons for each area and run them incrementally.
- Track coverage and expand tests to cover all critical paths and edge cases.

## 📋 **Immediate Next Steps Checklist**

### **1. Environment Setup**
- [ ] Install dependencies using `uv add -e .`
- [x] Activate the virtual environment: `source .venv/bin/activate`
- [x] Verify package installation: `meshic-pipeline --help` or `python -m meshic_pipeline.cli --help`
  - meshic-pipeline CLI is available and functional
- [x] Check database connectivity and configuration
  - Database is accessible and tables are present (see `list-tables` output)

### **2. Run Baseline 3x3 Riyadh Test**
- [x] Execute geometric pipeline: `meshic-pipeline geometric`
  - **Note:** Pipeline ran successfully for most layers, but failed for 'parcels' due to `invalid input syntax for type bigint: "9.0"` (zoning_id). All other layers processed and persisted as expected. This error must be fixed before scaling or enrichment.
- [x] Verify database population: Check that parcels and reference tables are populated
- [x] Validate schema: Confirm data types and foreign key relationships
- [ ] Monitor performance: Record processing time and memory usage

## Comprehensive Debugging & Remediation Plan for Pipeline/DB Issues (July 2025)

### Context
- The geometric pipeline runs, but the `parcels` and related tables are empty in the database.
- The pipeline logs show a type error for `zoning_id` (invalid input syntax for type bigint: "9.0").
- The stitched output for parcels (`stitched/parcels_stitched.geojson`) only contains `parcel_id` and `geometry`—all other expected columns are missing.
- Other layers (e.g., subdivisions, neighborhoods) are populated as expected.

### Goals
- Ensure all expected columns (especially `zoning_id`) are present and correctly typed in the stitched output and DB.
- Identify and fix the root cause of missing columns and type errors.
- Make the pipeline robust to similar issues in the future.

---

### Step-by-Step Actions for Investigation & Remediation

#### 1. **Verify Input Data Integrity**
- [ ] Inspect the raw decoded tiles for the `parcels` layer to confirm if fields like `zoning_id` are present in the source data.
    - Add debug logging or use a script to print all keys/properties from a sample of decoded parcel features.
- [ ] If fields are missing at this stage, investigate the tile source or decoding logic.

#### 2. **Check Decoding Logic**
- [ ] Review `MVTDecoder` and its `_cast_property_types` method:
    - Ensure it does not drop or mis-cast fields like `zoning_id`.
    - Confirm that all expected fields are retained in the output GeoDataFrames.
- [ ] Add logging to warn if any expected columns are missing after decoding.

#### 3. **Review Aggregation & Stitching**
- [ ] In `GeometryStitcher.stitch_geometries`, ensure that the aggregation step does not drop columns.
    - The aggregation rules in config should include all required fields.
    - Patch the code to always reindex the stitched GeoDataFrame to include all expected columns (from schema/config), filling with `None` if missing.
- [ ] Add warnings if columns are missing after aggregation.

#### 4. **Validate Type Casting Before DB Write**
- [ ] In `PostGISPersister._validate_and_cast_types`, confirm that float values like `9.0` for integer fields are cast to `9` (int), not left as float or string.
    - Add test cases for edge cases (e.g., string "9.0", float 9.0, int 9).
    - Add logging for any values that cannot be cast and are set to `None`.

#### 5. **Check Stitched Output Files**
- [ ] After running the pipeline, inspect the stitched GeoJSON for parcels:
    - Confirm all expected columns are present.
    - If not, trace back to which step they were dropped.

#### 6. **Database Schema & Constraints**
- [ ] Confirm the DB schema matches the expected model (already checked, but re-verify if changes are made).
- [ ] Ensure PostGIS extension is enabled and all migrations are up to date.

#### 7. **Improve Error Handling & Logging**
- [ ] Add clear error messages and warnings for any missing columns, type mismatches, or failed DB writes.
- [ ] Consider failing fast (with a clear message) if critical columns are missing at any stage.

#### 8. **Testing**
- [ ] Add/expand unit tests for:
    - Decoding logic (all expected fields present)
    - Type casting (robust to float/int/string edge cases)
    - Stitching/aggregation (columns not dropped)
- [ ] Add integration tests to run the full pipeline and check DB population.

#### 9. **Documentation**
- [ ] Document all findings, fixes, and any changes to the pipeline or schema.
- [ ] Update this TODO as issues are resolved.

---

### Additional Potentials to Explore
- [ ] Are there any upstream data changes (tile schema, API, etc.) that could have caused missing fields?
- [ ] Are there any recent code changes in decoding, aggregation, or DB writing logic?
- [ ] Is the pipeline running with the correct config/environment (e.g., not using a stale or test config)?
- [ ] Are there any silent failures or exceptions being swallowed in the pipeline?

---

### Handoff Notes
- This checklist is designed for another developer to pick up and systematically resolve the pipeline/DB issues.
- Please document all findings and fixes directly in this file or in a new issue tracker as appropriate.
- If you need more context, review the pipeline logs, stitched GeoJSONs, and the code in `src/meshic_pipeline/`.

## ✅ Baseline Validation Results (July 2025)
- All tests run successfully (`unit_test_results.txt`)
- Geometric pipeline completed for 3x3 Riyadh grid (9,007 parcels)
- Enrichment pipeline completed for 100 parcels (must use `PYTHONPATH=$(pwd)` workaround)
- No critical errors in logs or test output
- Only non-blocking issue: Pydantic deprecation warning (Field extra keys: 'env')

## 📋 **Immediate Next Steps Checklist**

- [x] Install and activate environment
- [x] Run geometric pipeline for 3x3 grid
- [x] Validate DB and schema
- [x] Run enrichment pipeline
- [x] Expand/run tests
- [x] Check logs for errors (none found)
- [ ] Update documentation and memory bank
- [ ] Prepare for multi-province validation

## Notes
- Enrichment pipeline must be run as:
  ```bash
  PYTHONPATH=$(pwd) python src/meshic_pipeline/run_enrichment_pipeline.py fast-enrich --limit 100
  ```
- Pydantic deprecation warning is present but does not affect current functionality.
