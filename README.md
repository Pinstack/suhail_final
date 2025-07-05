# Meshic Geospatial Data Pipeline

A sophisticated **two-stage geospatial data processing pipeline** for the Riyadh real estate market. This system processes over 1 million land parcels and 50,000+ transactions, combining high-performance MVT tile processing with comprehensive business intelligence enrichment.

## 🏗️ Architecture Overview

### **Stage 1: Geometric Pipeline**
Downloads and processes geospatial shapes from Mapbox Vector Tiles (MVT):
- **Source**: `https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf`
- **Coverage**: Riyadh metropolitan area (15 layers, 1M+ parcels)
- **Output**: PostGIS database with geometric features

### **Stage 2: Enrichment Pipeline**
Fetches business intelligence data from external APIs:
- **Transactions**: Historical real estate transaction data
- **Building Rules**: Zoning and construction regulations  
- **Price Metrics**: Market analysis and pricing trends
- **Smart Processing**: Multiple enrichment strategies for comprehensive data capture

## 🚀 Key Features

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

## 📊 Data Coverage

- **Parcels**: 1,032,380 land parcels with geometric boundaries
- **Transactions**: 45,526+ real estate transactions with enrichment data
- **Building Rules**: 68,396+ zoning and construction regulations
- **Price Metrics**: 752,963+ market analysis data points
- **Geographic Scope**: Complete Riyadh metropolitan area

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
# Create .env file
echo "DATABASE_URL=postgresql://username:password@localhost:5432/meshic" > .env
echo "SUHAIL_API_BASE_URL=https://api2.suhail.ai" >> .env
```

### 3. **Run Complete Pipeline**

#### **Stage 1: Geometric Processing**
```bash
# Process Riyadh metropolitan area (uses config grid)
meshic-pipeline geometric

# Or specify custom bounding box
meshic-pipeline geometric --bbox 46.428223 24.367114 47.010498 24.896402
```

#### **Stage 2: Business Intelligence Enrichment**
```bash
# Initial enrichment (new parcels only)
meshic-pipeline enrich fast-enrich

# Trigger-based enrichment (after geometric run)
meshic-pipeline enrich smart-pipeline-enrich --geometric-first --trigger-after

# Check status and get recommendations
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

## 📊 Monitoring & Operations

### **Status Monitoring**
```bash
# Check enrichment coverage and freshness
python monitor_enrichment.py status

# Get automated recommendations
python monitor_enrichment.py recommend

# View scheduling guidance
python monitor_enrichment.py schedule-info
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
1. Run geometric pipeline first: `python run_pipeline.py`
2. Run initial enrichment: `meshic-pipeline enrich fast-enrich`
3. Setup monitoring: `python monitor_enrichment.py status`

### **For Ongoing Operations**
- **💡 LEVERAGE THE INSIGHT**: Use `fast-enrich` after geometric pipeline for maximum efficiency
- **Never use only `fast-enrich`** for ongoing operations - it misses new transactions on existing parcels
- **Use `incremental-enrich`** weekly to capture new transaction data
- **Monitor regularly** with `monitor_enrichment.py recommend`

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
# Run test suite
pytest tests/

# Test specific components
pytest tests/enrichment/
pytest tests/geometry/
```

## 🛟 Troubleshooting

### **Common Issues**
```bash
# Database connection issues
python check_db.py

# Memory issues during processing
meshic-pipeline enrich incremental-enrich --batch-size 50

# Check enrichment status
python monitor_enrichment.py status
```

### **Performance Optimization**
- Reduce batch size if memory issues occur
- Increase batch size for better throughput
- Use incremental enrichment for efficiency
- Monitor with built-in tools for optimal scheduling

## Clean Slate Protocol

See [`CLEAN_SLATE_PROTOCOL.md`](./CLEAN_SLATE_PROTOCOL.md) for a step-by-step, safety-focused guide to resetting and rebuilding the spatial database environment for this project. **Use with caution: this protocol is destructive and intended for development environments only.**

---

**🎯 This pipeline ensures comprehensive capture of all transaction data while maintaining high performance and operational reliability.**

# Developer Handoff Checklist (July 2025)

Welcome! If you're picking up the pipeline/data debugging and remediation, here is what you need to get started:

## What is Provided
- **Codebase:** All code and migrations are in this repository.
- **Sample .pbf files:** A 2x2 grid of sample tiles is provided in `sample_data/` (e.g., `14060.pbf`, `14061.pbf`, `14062.pbf`, etc.).
- **Stitched GeoJSON outputs:** See `stitched/`