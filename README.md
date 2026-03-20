[![CI](https://github.com/<your-org-or-username>/<your-repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-org-or-username>/<your-repo>/actions/workflows/ci.yml)

# Meshic Geospatial Data Pipeline

A sophisticated **two-stage geospatial data processing pipeline** for the Saudi real estate market. The pipeline is now fully database-driven: all tiles to be processed are stored in the `tile_urls` table, supporting province-wide and all-Saudi scrapes with resumable, robust processing.

## 🏗️ Architecture Overview

### **Stage 1: Geometric Pipeline (DB-Driven)**
- Downloads and processes geospatial shapes from Mapbox Vector Tiles (MVT)
- **Tile discovery and orchestration is now fully managed via the `tile_urls` table in the database**
- Supports province-wide and all-Saudi scrapes
- Pipeline can be stopped and resumed, processing only pending/failed tiles

### **Stage 2: Enrichment Pipeline**
- Fetches business intelligence data from external APIs
- Status tracking and enrichment are managed via the database

## 🚀 Key Features

### **DB-Driven Tile Discovery and Orchestration**
- All tiles to be processed are stored in the `tile_urls` table
- Pipeline entry point queries the database for pending/failed tiles
- Status updates and resumability are managed via the database
- Province-wide and all-Saudi scrapes are now possible and robust

### **Geometric Processing**
- **Asynchronous Downloads**: High-performance MVT tile processing with `aiohttp`
- **Grid-Based Processing**: Configurable tile grid system for large-scale coverage
- **Geometry Stitching**: Advanced tile boundary processing and validation
- **PostGIS Integration**: Robust spatial data storage with PostgreSQL/PostGIS

### **Business Intelligence Enrichment**
- **Multi-Strategy Enrichment**: New parcels, incremental updates, and full refresh modes
- **Transaction Capture**: Guaranteed capture of new transactions on existing parcels
- **Smart Monitoring**: Automated recommendations for optimal enrichment schedules
- **Performance Optimized**: Concurrent API processing with 200+ connection limits

### **Operational Excellence**
- **Database Migrations**: Structured schema management
- **Monitoring Tools**: Real-time status tracking and recommendations
- **CLI Interface**: Multiple command options for different operational needs
- **Testing Framework**: Comprehensive `pytest` environment

## 📊 Data Coverage (Production)

- Parcels: 2,163,003
- Transactions: 70,787
- Building Rules: 130,112
- Price Metrics: 76,080,728
- Geographic Scope: 12 provinces (812 neighborhoods)

## ✅ **API Integration Status: FULLY OPERATIONAL**

### **Real Suhail API Endpoints**
- **Base URL**: `https://api2.suhail.ai` ✅ Working
- **Building Rules**: `/parcel/buildingRules` ✅ Arabic zoning data
- **Price Metrics**: `/api/parcel/metrics/priceOfMeter` ✅ Multi-category pricing
- **Transactions**: `/transactions` ✅ Historical transaction records

### **Recent Achievements**
- **🎉 Zero 404 Errors**: All API endpoints responding correctly
- **💰 Transaction Storage**: Real transaction data captured and stored
- **🏗️ Building Rules**: Arabic zoning categories properly processed
- **📊 Price Metrics**: Market analysis data flowing successfully

## 🛠️ Prerequisites

- **Python**: 3.9+
- **Database**: PostgreSQL with PostGIS extension
- **Memory**: 8GB+ RAM recommended for large-scale processing
- **Network**: Stable internet connection for API enrichment

## ⚡ Quick Start

### 1. **Environment Setup**
```bash
# Clone and setup
git clone <your-repo-url>
cd <project-directory>

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .
```

### 2. **Database Configuration**
```bash
# Local secrets: copy template (never commit .env — it is gitignored)
cp .env.example .env
# Edit DATABASE_URL for your Postgres/PostGIS instance.

# Optional — enrichment API base URL when running Stage 2:
# echo "SUHAIL_API_BASE_URL=https://api2.suhail.ai" >> .env
```

### 3. **Run Complete Pipeline**

#### Stage 1: Geometric Processing (DB-driven)
```bash
# Seed tiles (optional; per province or all provinces)
meshic-pipeline seed-tiles --province riyadh --limit 1000 --stride 2

# Process tiles using the DB queue (recommended)
meshic-pipeline db-geometric --batch-size 1000 --concurrency 5 --adaptive

# Or traditional bbox mode
meshic-pipeline geometric --bbox 46.428223 24.367114 47.010498 24.896402
```

#### Stage 2: Enrichment
```bash
# Fast enrichment (new parcels that need data)
meshic-pipeline fast-enrich --batch-size 200

# Incremental enrichment (stale by days)
meshic-pipeline incremental-enrich --days-old 30 --batch-size 100

# Delta enrichment (only parcels with price changes)
meshic-pipeline delta-enrich --auto-geometric

# Monitoring
meshic-pipeline monitor status
meshic-pipeline monitor recommend
```

## 🔄 Enrichment Strategies

### **💡 KEY INSIGHT: Stage 1 Reveals Transaction Data**
The geometric pipeline (Stage 1) already identifies which parcels have transactions via the `transaction_price > 0` field from MVT tiles. This makes enrichment **93.3% more efficient** by only processing the 69,584 parcels (6.7%) that actually need enrichment instead of all 1M+ parcels!

The pipeline provides **multiple enrichment modes** to leverage this insight:

### **🎯 TRIGGER-BASED** (Maximum Efficiency)
```bash
meshic-pipeline enrich fast-enrich --batch-size 400
```
 - **🚀 Leverages your insight**: Only processes parcels with `transaction_price > 0`
- **93.3% efficiency gain**: Skips 962,796 parcels that don't need enrichment
- Perfect for post-geometric pipeline runs
- **Use case**: Maximum efficiency, best performance

### **🆕 NEW PARCELS** (Standard Approach)
```bash
meshic-pipeline enrich fast-enrich --batch-size 200
```
- Processes parcels never enriched before (same as trigger-based but different implementation)
- Perfect for initial runs or capturing new parcels
- **Use case**: Daily operations, initial deployment

### **🔄 INCREMENTAL UPDATES** (Weekly/Monthly) 
```bash
# Weekly updates (recommended)
meshic-pipeline enrich incremental-enrich --days-old 7 --batch-size 100

# Monthly updates
meshic-pipeline enrich incremental-enrich --days-old 30 --batch-size 100
```
- **🎯 Captures new transactions on existing parcels**
- Re-processes parcels not enriched recently
- **Use case**: Ongoing operations to catch new transaction data

### **🔥 FULL REFRESH** (Quarterly)
```bash
meshic-pipeline enrich full-refresh --batch-size 50
```
- Re-processes ALL enrichable parcels
- Guarantees 100% data completeness
- **Use case**: Quarterly data validation, major updates

### **🎯 DELTA ENRICHMENT** (Revolutionary Precision) 
```bash
# Automatic workflow (recommended)
meshic-pipeline enrich delta-enrich --auto-geometric

# Manual workflow (if fresh MVT data already exists)
meshic-pipeline enrich delta-enrich

# Testing with limits
meshic-pipeline enrich delta-enrich --limit 100 --auto-geometric
```
- **🚀 MVT-based change detection**: Only enriches parcels with actual transaction price changes
- **Perfect precision**: No false positives from time-based approaches
- **Real market signals**: Detects new parcels, price changes, null→positive transitions  
- **Ultimate efficiency**: Maximum resource optimization
- **Auto-geometric**: Automatically runs geometric pipeline to get fresh MVT data
- **Use case**: Automated monthly/weekly runs, maximum precision operations
- **Consistent errors**: Follows `❌ ERROR`/`💡 HINT` pattern for all CLI failures
- **Metrics logged**: Summary statistics and structured JSON are printed at the end of each run
- **Temp table cleanup**: Auto-created tables are dropped on success or failure

## 📊 Monitoring & Operations

### Status Monitoring (CLI)
```bash
# Queue status, enrichment coverage, failures
meshic-pipeline monitor status

# Automated recommendations
meshic-pipeline monitor recommend

# Scheduling guidance
meshic-pipeline monitor schedule-info

# Reset stale in_progress tiles (for cron)
meshic-pipeline monitor reset-stale -- --stale-minutes 60

# Sample performance measurements (writes docs/reports)
meshic-pipeline monitor perf -- --label baseline --iterations 5

# Repair missing province metadata (tile URL/bbox)
python scripts/util/backfill_province_metadata.py --province-id 21012
```

### **Recommended Operational Schedule**

| Frequency | Command | Purpose |
|-----------|---------|---------|
| **After Geometric** | `fast-enrich` | **🚀 Maximum efficiency** - leverage transaction_price > 0 |
| **Daily** | `fast-enrich` | Capture new parcels (standard approach) |
| **Weekly** | `incremental-enrich --days-old 7` | **Capture new transactions** |
| **Weekly/Monthly** | `delta-enrich --auto-geometric` | **🎯 Ultimate precision** - MVT change detection |
| **Monthly** | `incremental-enrich --days-old 30` | Ensure data freshness |
| **Quarterly** | `full-refresh` | Complete data validation |

## 🗃️ Database Schema

### **Core Tables**
- `parcels`: Land parcel geometries with transaction prices
- `transactions`: Historical real estate transaction data  
- `building_rules`: Zoning and construction regulations
- `parcel_price_metrics`: Market analysis and pricing trends
- `neighborhoods`: Administrative boundary data

### **Performance Features**
- **Spatial Indexes**: GIST indexes on all geometry columns
- **Conflict Resolution**: `ON CONFLICT DO NOTHING` for data integrity
- **Enrichment Tracking**: `enriched_at` timestamps for smart updates

## 🔧 Advanced Configuration

### **Pipeline Configuration** (`pipeline_config.yaml`)
```yaml
# Riyadh metropolitan area grid
center_x: 20636      # Tile grid center X  
center_y: 14069      # Tile grid center Y
grid_w: 52           # Grid width (tiles)
grid_h: 52           # Grid height (tiles) 
zoom: 15             # Zoom level
layers: [parcels, transactions, neighborhoods, ...]
```

### **Performance Tuning**
```bash
# High-performance settings
meshic-pipeline enrich incremental-enrich \
  --batch-size 500 \
  --days-old 7

# Memory-optimized settings
meshic-pipeline enrich incremental-enrich \
  --batch-size 100 \
  --days-old 7
```

### Memory Management

Two configuration values control memory usage:

- `MAX_MEMORY_MB` – soft memory limit before garbage collection is triggered.
- `ENABLE_MEMORY_MONITORING` – toggle automatic memory checks.

Both can be set in your `.env` file or overridden with the `--max-memory` and
`--enable-monitoring/--disable-monitoring` options of `run_geometric_pipeline.py`.

## 🎯 Critical Features for Production

### **Transaction Capture Guarantee**
The pipeline **guarantees** capture of new transactions through:
- **Smart parcel selection**: Age-based re-processing
- **Conflict resolution**: Prevents duplicate data 
- **Monitoring tools**: Automated recommendations
- **Multiple strategies**: Covers all operational scenarios

### **Operational Reliability**  
- **Error handling**: Graceful handling of API failures
- **Memory management**: Optimized for large-scale processing
- **Performance monitoring**: Real-time status tracking
- **Database integrity**: ACID compliance with conflict resolution

## 🚨 Important Notes

### **For New Deployments**
1. Seed provinces (optional): `meshic-pipeline seed-tiles --province riyadh`
2. Run geometric pipeline: `meshic-pipeline db-geometric`
3. Run initial enrichment: `meshic-pipeline fast-enrich`
4. Setup monitoring: `meshic-pipeline monitor status`

### **For Ongoing Operations**
- **💡 LEVERAGE THE INSIGHT**: Use `fast-enrich` after geometric pipeline for maximum efficiency
- **Never use only `fast-enrich`** for ongoing operations - it misses new transactions on existing parcels
- **Use `incremental-enrich`** weekly to capture new transaction data
- **Monitor regularly** with `uv run meshic-pipeline monitor recommend`

### **🚀 EFFICIENCY BREAKTHROUGH**
Your insight reveals a **93.3% efficiency gain**:
- **Traditional approach**: Process all 1,032,380 parcels
- **Your approach**: Only process 69,584 parcels with `transaction_price > 0`
- **Result**: Skip 962,796 parcels that don't need enrichment!

## 📈 Performance Metrics

- **Geometric Processing**: ~2.7M features in 15 layers
- **Enrichment Speed**: 1,000+ parcels/minute with optimized settings
- **Database Performance**: 1M+ records with sub-second spatial queries
- **API Efficiency**: 200+ concurrent connections with retry logic

## 🧪 Testing

```bash
uv run pytest

uv run pytest tests/unit
uv run pytest tests/integration
```

## 🛟 Troubleshooting

### Common Issues
```bash
# Database connection issues
check_db

# Memory issues during processing
meshic-pipeline incremental-enrich --batch-size 50

# Check enrichment status
meshic-pipeline monitor status
```

### **Performance Optimization**
- Reduce batch size if memory issues occur
- Increase batch size for better throughput
- Use incremental enrichment for efficiency
- Monitor with built-in tools for optimal scheduling

## Clean Slate Protocol

See [`CLEAN_SLATE_PROTOCOL.md`](./docs/CLEAN_SLATE_PROTOCOL.md) for a step-by-step, safety-focused guide to resetting and rebuilding the spatial database environment for this project. **Use with caution: this protocol is destructive and intended for development environments only.**

---

**🎯 This pipeline ensures comprehensive capture of all transaction data while maintaining high performance and operational reliability.**

# Developer Handoff Checklist (July 2025)

Welcome! If you're picking up the pipeline/data debugging and remediation, here is what you need to get started:

## What is Provided
- **Codebase:** All code and migrations are in this repository.
- **Sample .pbf files:** A 2x2 grid of sample tiles is provided in `sample_data/` (e.g., `14060.pbf`, `14061.pbf`, `14062.pbf`, etc.).
- **Stitched GeoJSON outputs:** See `stitched/`

## ✅ Baseline Validation Status (July 2025)
- All tests passed (`unit_test_results.txt`)
- Geometric pipeline completed for 3x3 Riyadh grid (9,007 parcels)
- Enrichment pipeline completed for 100 parcels (see workaround below)
- No critical errors in logs or test output
- Only non-blocking issue: Pydantic deprecation warning (Field extra keys: 'env')

## ⚠️ Troubleshooting

### Enrichment Pipeline Import Error
If you see `ModuleNotFoundError: No module named 'src'` when running enrichment via the CLI, use this workaround:

```bash
PYTHONPATH=$(pwd) python src/meshic_pipeline/run_enrichment_pipeline.py fast-enrich --limit 100
```

This is required because the CLI currently invokes the enrichment script as a subprocess, which does not set up the Python path correctly. This will be fixed in a future release.

### Pydantic Deprecation Warning
You may see a warning like:
```
PydanticDeprecatedSince20: Using extra keyword arguments on `Field` is deprecated and will be removed. Use json_schema_extra instead. (Extra keys: 'env').
```
This does not affect current functionality but should be addressed in the future for compatibility.

## 🆕 Province Sync & Schema Requirements

### Province Data Sync
- The pipeline now requires up-to-date province data from the authoritative Suhail API.
- Before running the geometric or enrichment pipeline, run:
  ```bash
  source .venv/bin/activate
  python scripts/util/sync_provinces.py
  ```
- This script fetches and upserts all provinces from https://api2.suhail.ai/regions, ensuring all referenced province IDs are present.
- The sync is also integrated at the start of the geometric pipeline for safety.

### Schema Requirements
- The `parcels` table must include a `region_id` column of type BIGINT (nullable).
- If you update models, always update the Alembic migration baseline.

## ⚙️ Automation & CI/CD
- For reproducibility, add the following to your CI/CD pipeline:
  1. **Reset DB** (drop/create, migrate, enable PostGIS)
  2. **Run province sync** (`python scripts/util/sync_provinces.py`)
  3. **Run geometric pipeline**
  4. **Run enrichment pipeline**
- Optionally, schedule the province sync as a cron job if the DB is long-lived.

## 🛠️ CLI Command Reference (Full Surface)

> **For a complete audit and up-to-date matrix, see [`docs/CLI_COMMAND_AUDIT.md`](docs/CLI_COMMAND_AUDIT.md).**

### Core Commands

- `meshic-pipeline geometric [--bbox ...] [--recreate-db] [--save-as-temp ...]`
  - Run geometric pipeline (Stage 1)
  - Options:
    - `--bbox min_lon min_lat max_lon max_lat` — Bounding box for processing
    - `--recreate-db` — Drop and recreate the database schema
    - `--save-as-temp <table>` — Save parcels to a temporary table

- `meshic-pipeline fast-enrich [--batch-size ...] [--limit ...]`
  - Enrich new parcels with transaction prices
  - Options:
    - `--batch-size <int>` — Number of parcels per batch (default: 200)
    - `--limit <int>` — Limit parcels for testing

- `meshic-pipeline incremental-enrich [--batch-size ...] [--days-old ...] [--limit ...]`
  - Enrich parcels not updated in X days
  - Options:
    - `--batch-size <int>` — Number of parcels per batch (default: 100)
    - `--days-old <int>` — Days old threshold (default: 30)
    - `--limit <int>` — Limit parcels for testing

- `meshic-pipeline full-refresh [--batch-size ...] [--limit ...]`
  - Enrich ALL parcels (complete refresh)
  - Options:
    - `--batch-size <int>` — Number of parcels per batch (default: 50)
    - `--limit <int>` — Limit parcels for testing

- `meshic-pipeline delta-enrich [--batch-size ...] [--limit ...] [--fresh-table ...] [--auto-geometric] [--show-details/--no-details]`
  - Only process parcels with actual transaction price changes
  - Options:
    - `--batch-size <int>` — Number of parcels per batch (default: 200)
    - `--limit <int>` — Limit parcels for testing
    - `--fresh-table <table>` — Fresh MVT table name (default: parcels_fresh_mvt)
    - `--auto-geometric` — Auto-run geometric pipeline first
    - `--show-details/--no-details` — Show change analysis (default: show)

### Advanced/Composite Commands

- `meshic-pipeline smart-pipeline [--geometric-first] [--batch-size ...] [--bbox ...]`
  - Complete geometric + enrichment workflow (recommended for full runs)

- `meshic-pipeline monitor <status|recommend|schedule-info>`
  - Run enrichment monitoring commands

- `meshic-pipeline province-geometric <province> [--strategy ...] [--recreate-db] [--save-as-temp ...]`
  - Geometric pipeline for a specific province
  - Options:
    - `province` — Province name (al_qassim, riyadh, madinah, asir, eastern, makkah)
    - `--strategy <str>` — Discovery strategy (optimal, efficient, comprehensive; default: optimal)
    - `--recreate-db` — Drop and recreate the database schema
    - `--save-as-temp <table>` — Save parcels to a temporary table

- `meshic-pipeline saudi-arabia-geometric [--strategy ...] [--recreate-db] [--save-as-temp ...]`
  - Geometric pipeline for ALL Saudi provinces

- `meshic-pipeline discovery-summary`
  - Show province discovery capabilities/statistics

- `meshic-pipeline province-pipeline <province> [--strategy ...] [--batch-size ...] [--geometric-first]`
  - Complete province pipeline: geometric + enrichment for specific province

- `meshic-pipeline saudi-pipeline [--strategy ...] [--batch-size ...] [--geometric-first]`
  - Complete Saudi Arabia pipeline: ALL provinces geometric + enrichment

### Usage Examples

```bash
# Run geometric pipeline for a bounding box
meshic-pipeline geometric --bbox 46.428223 24.367114 47.010498 24.896402

# Enrich new parcels (fast)
meshic-pipeline fast-enrich --batch-size 400

# Incremental enrichment (parcels not updated in 7 days)
meshic-pipeline incremental-enrich --days-old 7 --batch-size 100

# Full refresh (all enrichable parcels)
meshic-pipeline full-refresh --batch-size 50

# Delta enrichment (only parcels with price changes, auto-run geometric)
meshic-pipeline delta-enrich --auto-geometric

# Province-wide geometric processing
meshic-pipeline province-geometric riyadh --strategy optimal

# All-province geometric processing
meshic-pipeline saudi-arabia-geometric --strategy efficient

# Complete province pipeline (geometric + enrichment)
meshic-pipeline province-pipeline riyadh --strategy optimal --batch-size 300

# Complete Saudi pipeline (all provinces)
meshic-pipeline saudi-pipeline --strategy efficient --batch-size 500

# Show discovery summary
meshic-pipeline discovery-summary

# Monitor enrichment status
meshic-pipeline monitor status
```

## 🧪 Running Tests

To run all tests (including CLI tests) locally:

```bash
uv run pytest

uv run pytest tests/unit/test_cli_commands.py
```

All tests are run automatically in CI on every push and pull request.
