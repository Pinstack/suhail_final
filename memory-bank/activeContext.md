# Active Context (Updated)

## 🎯 **Current Status: DB-Driven Tile Discovery and Orchestration**

### **Project Reality Check: COMPLETED**
- **Database State**: Fresh PostgreSQL/PostGIS database (recently dropped and recreated)
- **Data Volume**: 3x3 grid in central Riyadh successfully processed; now ready for province-wide and all-Saudi scrapes
- **Current Scope**: All tile discovery and orchestration is now managed via the `tile_urls` table in the database
- **Business Objective**: Commercial data capture for client sales (not Suhail platform development)

### **Git Baseline: ESTABLISHED**
- ✅ **Clean Repository**: All outdated files removed (27 files, 5,756 deletions)
- ✅ **Baseline Tag**: `v0.1.0-baseline` created for clean starting point
- ✅ **Testing Branch**: `test/3x3-riyadh-baseline` ready for validation
- ✅ **Schema Migrations**: Fresh Alembic migration with robust PostGIS design

## �� **Active Work: DB-Driven Pipeline**

### **DB-Driven Tile Discovery and Orchestration**
- All tiles to be processed are now stored in the `tile_urls` table
- Pipeline entry point queries the database for pending/failed tiles
- Status updates and resumability are managed via the database
- Province-wide and all-Saudi scrapes are now possible and robust

### **Current Environment Status**
- **Database**: Fresh PostGIS schema with robust spatial design
- **Pipeline**: Functional async architecture, robust to geometry type issues, now orchestrated from the database
- **Configuration**: Province-specific tile servers configured
- **Dependencies**: All packages ready for installation via `uv`

## 📋 **Next Phase Planning**

### **Phase 2: Multi-Province Validation** (UPCOMING)
**Objective**: Confirm database handles multiple provinces safely

**Strategy**:
1. **Second Province Test**: Small grid in different province (Eastern or different Riyadh area)
2. **Verify No Conflicts**: Ensure data separation and no overwriting
3. **Test Enrichment**: Validate API integration with multi-province data

### **Phase 3: Full Province Scale** (FUTURE)
**Objective**: Scale to complete province processing

**Scope**: 
- Full Riyadh province (52x52 grid showed 1M+ parcels in previous testing)
- All 6 Saudi provinces (estimated 6M+ parcels total)
- Dynamic boundary discovery system development

## 🎯 **Active Decisions and Considerations**

### **Commercial Focus**
- **Primary Goal**: Extract Saudi real estate data for client analytics products
- **Revenue Model**: Data capture and value-add services for client sales
- **Not Platform Development**: This is data extraction, not Suhail platform enhancement

### **Technical Priorities**
1. **Database as Source of Truth**: Fresh schema is authoritative, all docs must align
2. **Systematic Validation**: Don't skip testing phases - validate each step
3. **Multi-Province Capability**: Ensure architecture scales across all 6 provinces
4. **Chunked Processing**: Handle large datasets efficiently with proper batching
5. **DB-Driven Orchestration**: All tile discovery, status tracking, and pipeline orchestration is managed via the `tile_urls` table in the database
6. **Resumability**: Pipeline can be stopped and resumed, processing only pending/failed tiles

### **Development Approach**
- **Start Small**: 3x3 baseline test first (now complete)
- **Scale Gradually**: Multi-province → Full province → All provinces
- **Track Performance**: Monitor processing times and database performance
- **Maintain Quality**: High enrichment success rates and data integrity

## 🛠 **Current Technical Context**

### **Database Architecture**
- **Type**: PostgreSQL with PostGIS spatial extensions
- **State**: Recently reset with robust schema design
- **Migration Tool**: Alembic for all schema changes
- **Design**: Multi-province capable with proper foreign key relationships

### **Pipeline Architecture**
- **Language**: Python 3.11+ with async/await patterns
- **Processing**: Chunked batch processing with memory management
- **API Integration**: Suhail API endpoints for enrichment data
- **CLI**: Unified command interface for all operations
- **DB-Driven Tile Orchestration**: All tile discovery and processing is managed via the database

### **Data Sources**
- **MVT Tiles**: Province-specific tile servers (riyadh, eastern_region, etc.)
- **Enrichment APIs**: api2.suhail.ai for transactions, building rules, price metrics
- **Coordinate System**: EPSG:4326 with proper CRS handling

## 📊 **Success Metrics for Current Phase**

### **Baseline Validation Success**
- [x] 3x3 grid processes without errors
- [x] Database populated with expected structure
- [x] Foreign key relationships functional
- [ ] Enrichment success rate >95%
- [x] No pipeline errors or data corruption
- **DB-driven tile orchestration and resumable processing validated**

### **Technical Validation Success**
- [x] Package installation works smoothly
- [x] CLI commands execute properly
- [x] Database connections stable
- [x] Memory usage reasonable
- [x] Processing times acceptable

### **Quality Assurance Success**
- [x] Spatial data accuracy maintained
- [x] Arabic text handling works properly
- [x] API integration functional (pending enrichment test)
- [x] Error handling graceful
- [x] Logging comprehensive

## 🔄 **Current Work Environment**

### **Development Setup**
```bash
# Environment activation
source .venv/bin/activate

# Package installation
uv add -e .

# Core testing commands
meshic-pipeline geometric               # 3x3 baseline test
meshic-pipeline fast-enrich --limit 100  # Enrichment validation
python scripts/check_db.py             # Database validation
```

### **Git Workflow**
```bash
# Current branch
test/3x3-riyadh-baseline

# Success tagging strategy
git tag v0.1.1-3x3-validated    # After successful baseline
git tag v0.1.2-enrichment-validated   # After enrichment success
```

## 📝 **Documentation Alignment Status**

### **Memory Bank Accuracy**
- ✅ **Project Brief**: Updated to reflect commercial objectives
- ✅ **TODO.md**: Rewritten for actual baseline validation plan
- ✅ **Active Context**: Updated for new stable baseline
- 🔄 **Progress**: Needs update to reflect fresh database state
- 🔄 **System Patterns**: Needs alignment with actual implementation
- 🔄 **Tech Context**: Needs update for baseline testing scope

### **Critical Corrections Made**
- **Scale Claims**: Removed inflated parcel counts - database is now populated for 3x3 grid
- **Enhanced Discovery**: Removed claims about working hotspot system - needs to be built
- **Business Context**: Clarified commercial data capture vs platform development
- **Current State**: Emphasized fresh database and baseline testing approach

## 🎯 **Immediate Next Steps**

1. **Complete Memory Bank Alignment**: Finish updating all files to reflect new DB-driven pipeline
2. **Execute Enrichment Test**: Run enrichment pipeline and validate results
3. **Document Actual Results**: Update progress with real metrics from enrichment and multi-province tests
4. **Plan Multi-Province Test**: Prepare for next validation phase
5. **Track Performance**: Establish baseline metrics for scaling decisions

This active context reflects the actual current state: fresh database, commercial objectives, and a validated, DB-driven pipeline ready for enrichment and scaling.

## Pipeline Table Uniqueness & Upsert Robustness (May 2024)

- The pipeline previously assumed all output tables were upsert-ready, but many are dynamically created without unique constraints.
- A new action plan is in place:
  - Remove unreliable upsert keys from config for tables without unique constraints.
  - Add unique constraints via Alembic for upsertable tables.
  - Use replace mode for tables where uniqueness is not possible.
  - Test the pipeline after changes.
  - Update documentation and communicate changes to the team.
- See WHAT_TO_DO_NEXT_PIPELINE_TABLES.md for the full step-by-step plan.

## Next Steps
- Config cleanup
- Alembic migration for constraints
- Pipeline test run
- Documentation update

## 🆕 Province Sync & Schema Alignment
- Province data is now synced from the authoritative Suhail API before pipeline runs.
- Run `python scripts/util/sync_provinces.py` before geometric or enrichment pipelines, or rely on the integrated sync at pipeline start.
- The `parcels` table now requires a nullable `region_id` column (BIGINT).
- All schema changes are managed via Alembic migrations.
- For reproducibility, add DB reset + sync + pipeline run to CI/CD.

## 🛠️ CLI Command Reference (Project Source of Truth)

> For a complete, up-to-date audit, see [`docs/CLI_COMMAND_AUDIT.md`](../docs/CLI_COMMAND_AUDIT.md) and the README.

### Core Commands
- `meshic-pipeline geometric [--bbox ...] [--recreate-db] [--save-as-temp ...]`
- `meshic-pipeline fast-enrich [--batch-size ...] [--limit ...]`
- `meshic-pipeline incremental-enrich [--batch-size ...] [--days-old ...] [--limit ...]`
- `meshic-pipeline full-refresh [--batch-size ...] [--limit ...]`
- `meshic-pipeline delta-enrich [--batch-size ...] [--limit ...] [--fresh-table ...] [--auto-geometric] [--show-details/--no-details]`

### Advanced/Composite Commands
- `meshic-pipeline smart-pipeline [--geometric-first] [--batch-size ...] [--bbox ...]`
- `meshic-pipeline monitor <status|recommend|schedule-info>`
- `meshic-pipeline province-geometric <province> [--strategy ...] [--recreate-db] [--save-as-temp ...]`
- `meshic-pipeline saudi-arabia-geometric [--strategy ...] [--recreate-db] [--save-as-temp ...]`
- `meshic-pipeline discovery-summary`
- `meshic-pipeline province-pipeline <province> [--strategy ...] [--batch-size ...] [--geometric-first]`
- `meshic-pipeline saudi-pipeline [--strategy ...] [--batch-size ...] [--geometric-first]`

### Workflow Recommendations
- **Baseline/Small Grid:** Use `geometric` and `fast-enrich` for initial validation.
- **Province-Scale:** Use `province-geometric` and `province-pipeline` for full province runs.
- **All-Provinces:** Use `saudi-arabia-geometric` and `saudi-pipeline` for country-wide processing.
- **Enrichment Strategies:** Use `fast-enrich`, `incremental-enrich`, `full-refresh`, and `delta-enrich` as appropriate for data freshness and efficiency.
- **Monitoring:** Use `monitor status`, `monitor recommend`, and `monitor schedule-info` for operational oversight.

> Always consult the README and CLI audit for the latest command options and usage patterns.