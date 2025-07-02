# Technical Context: Suhail Geospatial Pipeline

## Technology Stack

### **Core Technologies**
- **Language**: Python 3.11+ with async/await patterns
- **Database**: PostgreSQL 15+ with PostGIS spatial extensions
- **ORM**: SQLAlchemy 2.0+ with Alembic migrations
- **API Client**: aiohttp for async HTTP operations with session management
- **Spatial Processing**: GeoPandas, Shapely, pyproj for CRS handling
- **CLI**: Typer-based command interface (not Click)

### **External Dependencies**
- **MVT Tiles**: tiles.suhail.ai (Mapbox Vector Tile server)
- **Enrichment API**: api2.suhail.ai (transactions, zoning, pricing)
- **Tile Protocol**: MVT/PBF format at zoom level 15

## Current Architecture

### **Development Scale Configuration**
- **Grid Coverage**: 3x3 tile grid for testing/development
- **Data Volume**: 9,007 parcels across 19 database tables
- **Geographic Scope**: Central Riyadh test region (~3.7 km²)
- **Processing**: Async functional architecture with batch processing

### **Database Design**
```sql
-- Core Tables (19 total)
parcels (9,007 records)           -- Main parcel geometries and attributes
provinces (1 record)              -- Administrative regions  
municipalities (2 records)        -- Local government areas
neighborhoods (7 records)         -- District boundaries
subdivisions (34 records)         -- Subdivision boundaries
zoning_rules (32 records)         -- Land use regulations
land_use_groups (21 records)      -- Land use categories

-- Enrichment Tables (OPERATIONAL)
transactions (1 record)           -- Real estate transaction history
building_rules (289 records)      -- Construction regulations  
price_metrics (480 records)       -- Market pricing data
```

### **Performance Characteristics**
- **Spatial Queries**: Sub-second response on current 9K dataset
- **MVT Processing**: 9 tiles decoded successfully
- **Enrichment Success**: 99.3% coverage (289/291 parcels)
- **API Integration**: All 3 endpoints working with data quality filtering
- **Concurrency**: Async processing with aiohttp session management

## Enrichment Architecture ⭐ **CORRECTED IMPLEMENTATION**

### **Functional Async Design** (Not Class-Based)
```python
# Strategy Functions (async functions, not classes)
from meshic_pipeline.enrichment.strategies import (
    get_unprocessed_parcel_ids,        # New parcels needing enrichment
    get_stale_parcel_ids,              # Parcels with old data  
    get_delta_parcel_ids,              # MVT-based change detection
    get_all_enrichable_parcel_ids,     # Full refresh selection
    get_delta_parcel_ids_with_details  # Change analysis with stats
)

# API Client (session-based, not config-based)
async with aiohttp.ClientSession() as session:
    client = SuhailAPIClient(session)  # Takes session, not config
    
# Processing (async generator, not class)
from meshic_pipeline.enrichment.processor import fast_worker

# Persistence (async function, not class)  
from meshic_pipeline.persistence.enrichment_persister import fast_store_batch_data
```

### **Database Connection Pattern** ⭐ **CORRECTED SIGNATURE**
```python
from meshic_pipeline.persistence.db import get_async_db_engine

# Correct usage (takes 0 parameters)
engine = get_async_db_engine()  # Uses global settings, no parameters

# NOT: engine = get_async_db_engine(settings.database_url)  # WRONG
```

### **Complete Enrichment Workflow**
```python
# 1. Database Engine
engine = get_async_db_engine()

# 2. Strategy Selection  
parcel_ids = await get_unprocessed_parcel_ids(engine, limit=100)

# 3. API Processing
async with aiohttp.ClientSession() as session:
    client = SuhailAPIClient(session)
    
    # 4. Batch Processing (async generator)
    async for tx_batch, rules_batch, metrics_batch in fast_worker(parcel_ids, batch_size, client):
        
        # 5. Persistence
        async with get_session() as async_session:
            await fast_store_batch_data(async_session, tx_batch, rules_batch, metrics_batch)

# 6. Cleanup
await engine.dispose()
```

## Scaling Architecture (Future)

### **Production Scale Planning**
- **Target Coverage**: Expanded tile grid for metropolitan area
- **Database Optimization**: Partitioning and indexing for larger datasets
- **Performance Goals**: Maintain sub-second queries at city scale
- **Infrastructure**: Distributed processing capabilities

### **Scalability Patterns**
```python
# Current Pattern (Development)
grid_size = 3x3              # 9 tiles total
parcels = 9,007              # Test region
processing = "async_batch"   # Functional async with batching
success_rate = 99.3          # API quality filtering

# Future Pattern (Production)  
grid_size = "expandable"     # TBD based on testing
parcels = "city_scale"       # Full metropolitan area
processing = "distributed"   # Multiple async workers
success_rate = "99%+"        # Expect similar API filtering
```

## Development Setup

### **Environment Configuration**
```bash
# Required Environment Variables
DATABASE_URL=postgresql://user:pass@localhost/suhail_pipeline
SUHAIL_API_BASE_URL=https://api2.suhail.ai
TILE_BASE_URL=https://tiles.suhail.ai/maps/eastern_region
```

### **Project Structure** ⭐ **CORRECTED ARCHITECTURE**
```
src/meshic_pipeline/
├── config.py              # Centralized configuration
├── cli.py                 # Typer-based command interface
├── decoder/               # MVT tile processing
├── enrichment/           
│   ├── api_client.py      # SuhailAPIClient(session)
│   ├── strategies.py      # Async strategy functions
│   └── processor.py       # fast_worker async generator
├── persistence/          
│   ├── db.py              # get_async_db_engine() 
│   ├── models.py          # SQLAlchemy models
│   └── enrichment_persister.py  # fast_store_batch_data()
├── geometry/             # Spatial processing utilities
└── monitoring/           # Status tracking and recommendations
```

## API Integration ⭐ **VERIFIED WORKING**

### **Suhail API Endpoints**
- **Base URL**: https://api2.suhail.ai ✅ Verified
- **Transactions**: `/transactions?parcelObjectId={id}` ✅ Working
- **Building Rules**: `/parcel/buildingRules?parcelObjectId={id}` ✅ Working  
- **Price Metrics**: `/api/parcel/metrics/priceOfMeter` ✅ Working
- **Authentication**: API key based (optional for current endpoints)
- **Rate Limiting**: Respectful delays between requests
- **Error Handling**: Exponential backoff with retry logic

### **API Data Quality Filtering**
- **Behavior**: Suhail API filters unrealistic transaction prices
- **Example**: Parcels with $1.00 prices automatically rejected
- **Result**: 99.3% enrichment coverage (289/291 parcels)
- **Benefit**: Protects against garbage data in enrichment tables

### **Enrichment Strategies** ⭐ **CORRECTED CLI COMMANDS**
```bash
# Available CLI commands (verified working)
python -m meshic_pipeline.cli geometric           # Stage 1 pipeline
python -m meshic_pipeline.cli fast-enrich         # New parcels only
python -m meshic_pipeline.cli incremental-enrich  # Stale data refresh
python -m meshic_pipeline.cli full-refresh        # Complete refresh
python -m meshic_pipeline.cli delta-enrich        # Change detection
python -m meshic_pipeline.cli smart-pipeline      # Complete workflow
python -m meshic_pipeline.cli monitor status      # Status tracking
```

## Quality Assurance ⭐ **ENHANCED VALIDATION**

### **Data Validation**
- **Spatial Accuracy**: PostGIS geometry validation
- **Referential Integrity**: 4 foreign key relationships enforced
- **Type Safety**: SQLAlchemy model validation throughout pipeline
- **API Quality Control**: Suhail API filters invalid transaction prices
- **Unicode Support**: Perfect Arabic text handling (منطقة التقسيم س 111)

### **Performance Monitoring**
- **Enrichment Success Rate**: 99.3% (optimal with API filtering)
- **Query Performance**: Spatial index optimization
- **Memory Usage**: Async generator patterns prevent OOM
- **API Efficiency**: Session reuse and proper connection management
- **Error Tracking**: Comprehensive logging and exception handling

## Technical Constraints

### **Current Limitations**
- **Scale**: Currently limited to test region (3x3 grid)
- **Processing**: Single-instance deployment (ready for scale-up)
- **API Filtering**: 0.7% of parcels filtered by API (expected behavior)
- **Memory**: Generator patterns handle large datasets efficiently

### **Future Considerations**
- **Horizontal Scaling**: Multi-instance async processing
- **Caching Strategy**: Tile and API response caching
- **Monitoring Integration**: Production observability stack
- **Deployment Automation**: CI/CD pipeline implementation

## Enrichment Performance Metrics ⭐ **NEW SECTION**

### **Current Performance**
- **Success Rate**: 99.3% (289/291 parcels successfully enriched)
- **API Endpoints**: 3/3 endpoints working perfectly
- **Data Quality**: Perfect - no garbage data due to API filtering
- **Processing Speed**: Async batch processing with configurable concurrency
- **Error Handling**: Graceful failures with proper retry logic

### **Data Quality Statistics**
- **Transactions**: 1 record stored
- **Building Rules**: 289 records (Arabic text support)
- **Price Metrics**: 480 records with temporal data
- **Raw Data Preservation**: 100% for transactions and rules
- **Foreign Key Integrity**: 4/4 relationships properly maintained 