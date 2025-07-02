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
├── geometry/          # Tile stitching and validation
├── decoder/           # MVT processing and type casting
├── downloader/        # Async tile downloading
├── enrichment/        # API client and strategies
├── persistence/       # Database models and operations
├── monitoring/        # Status tracking and recommendations
└── cli.py            # Unified command interface
```

## Key Technical Decisions

### **1. Async Processing Pattern**
- **Choice**: `aiohttp` for concurrent operations
- **Rationale**: Handle 200+ simultaneous API connections
- **Implementation**: Semaphore-based concurrency control
- **Benefits**: Maximum throughput with controlled resource usage

### **2. Database-First Design**
- **Choice**: PostgreSQL with PostGIS extension
- **Rationale**: Native spatial operations and ACID compliance
- **Implementation**: SQLAlchemy ORM with Alembic migrations
- **Benefits**: Referential integrity and spatial indexing

### **3. Configuration-Driven Processing**
- **Choice**: YAML-based pipeline configuration
- **Rationale**: Flexible grid processing without code changes
- **Implementation**: Pydantic settings with environment overrides
- **Benefits**: Easy deployment across environments
- **API Configuration**: Real Suhail endpoints with proper URL structure

### **4. Multi-Strategy Enrichment**
- **Choice**: Multiple enrichment approaches
- **Rationale**: Different operational needs require different strategies
- **Implementation**: Strategy pattern with common interfaces
- **Benefits**: Optimized performance for each use case

## Component Relationships

### **Geometric Pipeline Flow**
```
TileEndpointDiscovery → AsyncTileDownloader → MVTDecoder → GeometryStitcher → PostGISPersister
```

### **Enrichment Pipeline Flow**
```
EnrichmentStrategies → SuhailAPIClient → EnrichmentProcessor → EnrichmentPersister
```

### **Data Models Hierarchy**
```
Province (1:N) → Municipality
Province (1:N) → Neighborhood (1:N) → Parcel (1:N) → Transaction
                                   → Parcel (1:N) → BuildingRule  
                                   → Parcel (1:N) → PriceMetric
```

## Design Patterns in Use

### **1. Factory Pattern**
- **Usage**: Creating different enrichment strategies
- **Location**: `enrichment/strategies.py`
- **Benefits**: Extensible strategy creation

### **2. Strategy Pattern**
- **Usage**: Multiple enrichment approaches
- **Implementation**: `get_delta_parcel_ids()`, `get_unprocessed_parcel_ids()`
- **Benefits**: Algorithm selection at runtime

### **3. Repository Pattern**
- **Usage**: Data access abstraction
- **Implementation**: `PostGISPersister`, `EnrichmentPersister`
- **Benefits**: Database technology independence

### **4. Observer Pattern**
- **Usage**: Performance monitoring and logging
- **Implementation**: `MemoryMonitor`, `LoggingUtils`
- **Benefits**: Separation of concerns for monitoring

## Performance Optimizations

### **1. Intelligent Parcel Selection**
- **93.3% Efficiency Gain**: Only process parcels with `transaction_price > 0`
- **Implementation**: Database queries with WHERE clauses
- **Impact**: Skip parcels that don't need enrichment

### **2. Spatial Indexing**
- **GIST Indexes**: On all geometry columns
- **Impact**: Sub-second spatial queries on 1M+ records

### **3. Batch Processing**
- **Chunked Operations**: Configurable batch sizes (50-500)
- **Memory Management**: Prevents OOM with large datasets

### **4. Connection Pooling**
- **Database**: SQLAlchemy pool with health checks
- **HTTP**: aiohttp session reuse
- **Benefits**: Reduced connection overhead

## Error Handling Patterns

### **1. Graceful Degradation**
- **API Failures**: Retry with exponential backoff
- **Database Issues**: Transaction rollback and recovery
- **Memory Pressure**: Automatic batch size reduction

### **2. Data Validation**
- **Type Casting**: At MVT decode and persistence layers
- **Referential Integrity**: Foreign key constraints
- **Conflict Resolution**: `ON CONFLICT DO NOTHING` patterns

### **3. Monitoring Integration**
- **Performance Logging**: Memory usage and timing
- **Status Reporting**: Real-time pipeline health
- **Recommendations**: Automated optimization suggestions 