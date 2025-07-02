# System Patterns: Suhail Geospatial Data Pipeline

## Architecture Overview

### **Two-Stage Pipeline Design**
```
Stage 1: Geometric Pipeline    →    Stage 2: Enrichment Pipeline
    ↓                                        ↓
MVT Tiles → PostGIS              PostGIS → API Enrichment → PostGIS
```

### **Modular Architecture**
```
src/meshic_pipeline/
├── discovery/         # ENHANCED: Province discovery + original tile discovery
│   ├── tile_endpoint_discovery.py      # Original grid/bbox discovery
│   └── enhanced_province_discovery.py  # NEW: Province-level discovery
├── geometry/          # Tile stitching and validation
├── decoder/           # MVT processing and type casting
├── downloader/        # Async tile downloading
├── enrichment/        # API client and async strategies
├── persistence/       # Database models and async operations
├── monitoring/        # Status tracking and recommendations
└── cli.py            # ENHANCED: Unified command interface with province support
```

## Key Technical Decisions

### **1. Functional Async Pattern** ⭐ **CORRECTED ARCHITECTURE**
- **Choice**: Functional async design over class-based OOP
- **Rationale**: Better performance for I/O-bound operations and simpler testing
- **Implementation**: Async functions with `aiohttp` and `asyncio`
- **Benefits**: Natural concurrency patterns and resource efficiency

**Enrichment Strategy Functions** (Not Classes):
```python
# Strategy Selection (async functions)
await get_unprocessed_parcel_ids(engine, limit=100)
await get_stale_parcel_ids(engine, days_old=30) 
await get_delta_parcel_ids(engine, fresh_mvt_table="parcels_fresh_mvt")
await get_all_enrichable_parcel_ids(engine, limit=1000)
await get_delta_parcel_ids_with_details(engine, fresh_mvt_table="parcels_fresh_mvt")
```

### **2. Session-Based API Client** ⭐ **CORRECTED ARCHITECTURE**
- **Choice**: `SuhailAPIClient(session)` taking aiohttp session
- **Rationale**: Proper connection pooling and resource management
- **Implementation**: Session passed at initialization, not config object
- **Benefits**: Controlled connection lifecycle and better error handling

```python
# API Client Pattern (session-based)
async with aiohttp.ClientSession() as session:
    client = SuhailAPIClient(session)
    transactions = await client.fetch_transactions(parcel_id)
    rules = await client.fetch_building_rules(parcel_id)
    metrics = await client.fetch_price_metrics([parcel_id])
```

### **3. Async Generator Processing** ⭐ **CORRECTED ARCHITECTURE**
- **Choice**: `fast_worker()` async generator over processor classes
- **Rationale**: Memory-efficient streaming of large datasets
- **Implementation**: Yields batched results for immediate persistence
- **Benefits**: Controlled memory usage and real-time progress

```python
# Processing Pattern (async generator)
async for tx_batch, rules_batch, metrics_batch in fast_worker(parcel_ids, batch_size, client):
    count = await fast_store_batch_data(session, tx_batch, rules_batch, metrics_batch)
```

### **4. Functional Persistence** ⭐ **CORRECTED ARCHITECTURE**
- **Choice**: `fast_store_batch_data()` function over persister classes
- **Rationale**: Simpler testing and more direct database operations
- **Implementation**: Single async function handling all enrichment tables
- **Benefits**: Atomic operations and simplified error handling

### **5. Database-First Design**
- **Choice**: PostgreSQL with PostGIS extension
- **Rationale**: Native spatial operations and ACID compliance
- **Implementation**: SQLAlchemy ORM with Alembic migrations
- **Benefits**: Referential integrity and spatial indexing

### **6. Configuration-Driven Processing**
- **Choice**: YAML-based pipeline configuration
- **Rationale**: Flexible grid processing without code changes
- **Implementation**: Pydantic settings with environment overrides
- **Benefits**: Easy deployment across environments
- **API Configuration**: Real Suhail endpoints with proper URL structure

### **6. Enhanced Command-Line Interface** ⭐ **ENHANCED COMPONENT**
- **Choice**: Unified CLI with province-level discovery capabilities
- **Implementation**: Typer-based CLI with backward compatibility
- **Enhancement**: 5 new commands for province and Saudi Arabia processing
- **Benefits**: Streamlined operations from single grid to complete country

**Original Commands (Unchanged)**:
```bash
# Existing geometric and enrichment commands work exactly as before
python -m meshic_pipeline.cli geometric --bbox 46.5 24.0 47.0 24.5
python -m meshic_pipeline.cli fast-enrich --batch-size 200
python -m meshic_pipeline.cli smart-pipeline
```

**Enhanced Discovery Commands (New)**:
```bash
# Province-specific processing
python -m meshic_pipeline.cli province-geometric riyadh --strategy efficient
python -m meshic_pipeline.cli province-pipeline al_qassim

# Complete Saudi Arabia processing  
python -m meshic_pipeline.cli saudi-arabia-geometric --strategy optimal
python -m meshic_pipeline.cli saudi-pipeline --strategy efficient

# Discovery capabilities
python -m meshic_pipeline.cli discovery-summary
```

**Command Integration Patterns**:
- **Backward Compatibility**: All existing commands unchanged
- **Progressive Enhancement**: New capabilities added without breaking changes
- **Strategy Selection**: Configurable performance vs. detail optimization
- **Scale Flexibility**: From single province to complete country processing

## Component Relationships

### **Geometric Pipeline Flow**
```
TileEndpointDiscovery → AsyncTileDownloader → MVTDecoder → GeometryStitcher → PostGISPersister
```

### **Enrichment Pipeline Flow** ⭐ **CORRECTED FLOW**
```
Strategy Functions → SuhailAPIClient(session) → fast_worker() → fast_store_batch_data()
```

**Detailed Enrichment Flow**:
```python
# 1. Strategy Selection
parcel_ids = await get_unprocessed_parcel_ids(engine, limit=100)

# 2. API Client Initialization  
async with aiohttp.ClientSession() as session:
    client = SuhailAPIClient(session)
    
    # 3. Batch Processing
    async for tx_batch, rules_batch, metrics_batch in fast_worker(parcel_ids, batch_size, client):
        
        # 4. Persistence
        await fast_store_batch_data(async_session, tx_batch, rules_batch, metrics_batch)
```

### **Data Models Hierarchy**
```
Province (1:N) → Municipality
Province (1:N) → Neighborhood (1:N) → Parcel (1:N) → Transaction
                                   → Parcel (1:N) → BuildingRule  
                                   → Parcel (1:N) → PriceMetric
```

## Design Patterns in Use

### **1. Strategy Pattern** ⭐ **CORRECTED IMPLEMENTATION**
- **Usage**: Multiple enrichment selection approaches
- **Implementation**: Async functions, not classes
- **Functions**: `get_delta_parcel_ids()`, `get_unprocessed_parcel_ids()`, etc.
- **Benefits**: Algorithm selection at runtime with async efficiency

### **2. Generator Pattern** ⭐ **NEW PATTERN**
- **Usage**: Memory-efficient data processing
- **Implementation**: `fast_worker()` async generator
- **Benefits**: Streaming processing of large datasets

### **3. Session Management Pattern** ⭐ **NEW PATTERN**
- **Usage**: HTTP connection lifecycle management
- **Implementation**: aiohttp session passed to client
- **Benefits**: Connection pooling and proper resource cleanup

### **4. Repository Pattern**
- **Usage**: Data access abstraction
- **Implementation**: `PostGISPersister`, `fast_store_batch_data()`
- **Benefits**: Database technology independence

### **5. Observer Pattern**
- **Usage**: Performance monitoring and logging
- **Implementation**: `MemoryMonitor`, `LoggingUtils`
- **Benefits**: Separation of concerns for monitoring

## Performance Optimizations

### **1. Intelligent Parcel Selection**
- **99.3% Success Rate**: Process only parcels with valid transaction prices
- **Implementation**: Database queries with WHERE clauses and API quality filtering
- **Impact**: Skip parcels that API will reject (e.g., $1.00 prices)

### **2. API Quality Filtering** ⭐ **NEW OPTIMIZATION**
- **Suhail API Behavior**: Automatically filters unrealistic transaction prices
- **Result**: 2 parcels with $1.00 prices correctly rejected by API
- **Benefit**: Maintains data quality and prevents garbage data

### **3. Async Batch Processing** ⭐ **CORRECTED OPTIMIZATION**
- **Pattern**: `fast_worker()` processes batches concurrently
- **Memory Management**: Generator pattern prevents OOM with large datasets
- **Concurrency**: Multiple API calls per batch with aiohttp session

### **4. Spatial Indexing**
- **GIST Indexes**: On all geometry columns
- **Impact**: Sub-second spatial queries on 9K+ records

### **5. Connection Pooling**
- **Database**: SQLAlchemy async pool with health checks
- **HTTP**: aiohttp session reuse with proper lifecycle
- **Benefits**: Reduced connection overhead

## Error Handling Patterns

### **1. Graceful Degradation**
- **API Failures**: Retry with exponential backoff
- **Database Issues**: Transaction rollback and recovery
- **Memory Pressure**: Generator pattern prevents OOM

### **2. Data Validation** ⭐ **ENHANCED VALIDATION**
- **API-Level Filtering**: Suhail API rejects invalid transaction prices
- **Type Casting**: At MVT decode and persistence layers
- **Referential Integrity**: 4 foreign key constraints enforced
- **Conflict Resolution**: `ON CONFLICT DO NOTHING` patterns

### **3. Monitoring Integration**
- **Performance Logging**: Memory usage and timing
- **Status Reporting**: Real-time pipeline health with 99.3% success tracking
- **Recommendations**: Automated optimization suggestions

## Async Architecture Benefits ⭐ **NEW SECTION**

### **Performance Benefits**
- **Concurrency**: Multiple API calls processed simultaneously
- **Resource Efficiency**: Proper session and connection management
- **Memory Management**: Generator patterns prevent memory bloat
- **Scalability**: Configurable batch sizes and concurrency limits

### **Code Quality Benefits**
- **Testability**: Functions easier to test than complex class hierarchies
- **Maintainability**: Clear separation of concerns with async patterns
- **Debugging**: Simpler call stacks and error tracing
- **Resource Safety**: Automatic cleanup with async context managers 

### **Enhanced Province Discovery System** ⭐ **NEW MAJOR COMPONENT**
- **Purpose**: Comprehensive Saudi Arabia coverage with optimized tile discovery
- **Location**: `src/meshic_pipeline/discovery/enhanced_province_discovery.py`
- **Capability**: 74,033 parcels across 6 provinces vs. original 2,000 (37x increase)
- **Integration**: Fully backward compatible with existing pipeline

**Enhanced Discovery Architecture**:
```
Province Discovery → Hotspot Database → Strategy Selection → Tile Coordinates
       ↓                    ↓                    ↓                    ↓
Al-Qassim (17,484)   Pre-computed        Efficient (Zoom 11)    184 Total
Asir (15,417)        Coordinates         Optimal (Zoom 13)      Hotspots
Riyadh (13,155)      Browser Traffic     Comprehensive (Z15)    Verified
Madinah (12,429)     Integration         Performance            Working
Eastern (8,118)      Pattern Matching    Optimization           Coordinates
Makkah (7,430)       Validation          Strategy               
```

**Discovery Strategies**:
- **Efficient**: Zoom 11 (4x fewer HTTP requests) - Large area discovery
- **Optimal**: Zoom 13 (balanced performance/detail) - Production processing  
- **Comprehensive**: Zoom 15 (maximum granularity) - High-precision extraction

**Integration Points**:
```python
# Enhanced pipeline orchestrator integration
async def run_pipeline(
    province: str = None,           # NEW: Province-specific discovery
    strategy: str = "optimal",      # NEW: Strategy selection
    saudi_arabia_mode: bool = False # NEW: Complete country processing
):
    if saudi_arabia_mode:
        tiles = get_saudi_arabia_tiles(strategy=strategy)
    elif province:
        tiles = get_enhanced_tile_coordinates(province=province, strategy=strategy)
    # Existing bbox and grid discovery unchanged
``` 