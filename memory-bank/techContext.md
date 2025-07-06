# Technical Context: Meshic Geospatial Pipeline

## 🛠️ **Technology Stack**

### **Core Technologies**
- **Language**: Python 3.11+ with async/await patterns for high-performance I/O
- **Database**: PostgreSQL 15+ with PostGIS spatial extensions
- **ORM**: SQLAlchemy 2.0+ with async support and Alembic for schema migrations
- **HTTP Client**: aiohttp for async session management and concurrent API calls
- **Spatial Processing**: GeoPandas, Shapely, pyproj for coordinate system handling
- **CLI Framework**: Typer-based command interface with comprehensive validation

### **External Dependencies**
- **MVT Tiles**: tiles.suhail.ai with province-specific endpoints (riyadh, eastern_region, etc.)
- **Enrichment API**: api2.suhail.ai (transactions, zoning rules, price metrics)
- **Tile Protocol**: MVT/PBF format at zoom level 15 for parcel-level detail
- **Coordinate System**: EPSG:4326 (WGS84) for spatial consistency

### **Development Environment**
- **Package Manager**: uv for fast dependency resolution and virtual environment management
- **Environment Management**: Virtual environment with source activation required
- **Database Interaction**: Always through Alembic for schema changes (never direct)
- **Configuration**: YAML-based with environment variable overrides

## 🏗️ **Architecture Overview**

### **Fresh Database Foundation**
- **State**: Recently dropped and recreated PostgreSQL/PostGIS database
- **Schema**: Robust spatial design with proper data type alignment
- **Migrations**: Single fresh Alembic migration for complete schema setup
- **Relationships**: 4 foreign key relationships designed for referential integrity

### **Pipeline Design Pattern**
- **Architecture**: Functional async design (not class-based OOP)
- **Processing**: Two-stage pipeline with geometric extraction followed by enrichment
- **Concurrency**: Controlled async operations with proper resource management
- **Error Handling**: Graceful degradation with retry logic and partial success handling

### **Data Flow Architecture**
```
Stage 1: MVT Tiles → Decode → Stitch → PostGIS
Stage 2: PostGIS → API Enrichment → Enhanced PostGIS
```

## 🔄 **Current Implementation Status**

### **Environment Setup: READY**
- **Package**: meshic-pipeline ready for installation via `uv add -e .`
- **Dependencies**: All required packages specified in pyproject.toml
- **Configuration**: Province-specific settings configured in pipeline_config.yaml
- **Database**: Fresh schema with spatial extensions enabled

### **Pipeline Components: IMPLEMENTED**
- **Tile Discovery**: Province-specific endpoint discovery with zoom level optimization
- **Async Downloads**: Concurrent tile downloading with connection pooling
- **MVT Decoding**: Protobuf decoding with proper CRS handling
- **Spatial Stitching**: Geometry merging with duplicate detection
- **Database Persistence**: Chunked batch operations with type safety

### **API Integration: CONFIGURED**
- **Client**: aiohttp-based SuhailAPIClient with session management
- **Endpoints**: Three enrichment APIs (transactions, building_rules, price_metrics)
- **Error Handling**: Retry logic with exponential backoff
- **Data Quality**: API-level filtering for realistic transaction prices

## 📊 **Current Validation Scope**

### **Phase 1: 3x3 Baseline Testing**
- **Grid Size**: 9 tiles in central Riyadh for pipeline validation
- **Expected Volume**: ~1,000-2,000 parcels for functional testing
- **Purpose**: Validate basic pipeline functionality with fresh database
- **Success Criteria**: Complete processing without errors, proper data population

### **Database Schema Testing**
- **Tables**: Core spatial tables (parcels, neighborhoods, subdivisions, etc.)
- **Reference Tables**: provinces, municipalities, zoning_rules, land_use_groups
- **Relationships**: 4 foreign key constraints to validate referential integrity
- **Data Types**: Proper alignment between MVT source and database storage

### **Performance Baseline Establishment**
- **Processing Time**: TBD for 9-tile processing
- **Memory Usage**: To be measured during baseline testing
- **Database Performance**: Expected sub-second queries on test data
- **Enrichment Success**: Target 95%+ success rate for API integration

## 🔧 **Configuration Management**

### **Environment Configuration**
```yaml
# pipeline_config.yaml structure
database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  name: ${DB_NAME:meshic_pipeline}

processing:
  max_concurrent_downloads: 5
  batch_size: 50
  db_chunk_size: 5000

provinces:
  riyadh:
    tile_server: "https://tiles.suhail.ai/maps/riyadh"
    zoom_level: 15
```

### **Development Workflow**
```bash
# Environment setup
source .venv/bin/activate
uv add -e .

# Core testing commands
meshic-pipeline geometric               # 3x3 baseline test
meshic-pipeline fast-enrich --limit 100  # Enrichment validation
python scripts/check_db.py             # Database validation
```

## 🚀 **Performance Optimization Patterns**

### **Async Concurrency Management**
- **Connection Limits**: Controlled concurrent downloads (max 5 simultaneous)
- **Session Pooling**: aiohttp session reuse with proper lifecycle management
- **Database Pooling**: SQLAlchemy async connection pool with health checks
- **Memory Management**: Generator patterns for large dataset processing

### **Chunked Processing Strategy**
- **Tile Processing**: Batch downloads with configurable concurrency
- **Database Operations**: Bulk inserts with 5,000 record chunks
- **API Calls**: Batch enrichment with 50-parcel groups
- **Memory Efficiency**: Streaming processing to prevent OOM conditions

### **Error Resilience Patterns**
- **Retry Logic**: Exponential backoff for transient failures
- **Partial Success**: Continue processing when individual items fail
- **Resource Cleanup**: Proper async context manager usage
- **Graceful Degradation**: Pipeline continues with partial data when possible

## 📈 **Scaling Considerations**

### **Current Scale: Testing Foundation**
- **Scope**: 3x3 grid (9 tiles) for baseline validation
- **Volume**: ~1,000-2,000 parcels expected for testing
- **Purpose**: Validate architecture before scaling

### **Future Scale: Province Level**
- **Target**: Full Riyadh province (52x52 grid showed 1M+ parcels previously)
- **Architecture**: Proven async patterns ready for scale-up
- **Optimization**: Chunked processing designed for large datasets

### **Full Scale: Saudi Arabia Coverage**
- **Scope**: All 6 provinces (Riyadh, Eastern, Madinah, Makkah, Al_Qassim, Asir)
- **Estimated Volume**: 6M+ parcels based on Riyadh extrapolation
- **Approach**: Province-by-province rollout with performance monitoring

## 🔍 **Data Quality and Validation**

### **Schema Validation**
- **Type Safety**: Proper data types aligned with MVT source format
- **Spatial Integrity**: PostGIS validation for geometry data
- **Referential Integrity**: Foreign key constraints for data consistency
- **Unicode Support**: Proper Arabic text handling and storage

### **API Integration Quality**
- **Data Filtering**: API-level quality filters for transaction prices
- **Response Validation**: Proper handling of API responses and errors
- **Rate Limiting**: Respectful API usage with controlled concurrency
- **Error Handling**: Graceful handling of API failures and retries

### **Performance Monitoring**
- **Processing Metrics**: Timing and throughput measurement
- **Memory Usage**: Resource consumption tracking
- **Success Rates**: Enrichment pipeline success percentage
- **Error Tracking**: Comprehensive logging for issue diagnosis

## 🏛️ **Development Infrastructure**

### **Database Management**
- **Migration Tool**: Alembic for all schema changes
- **Version Control**: Git-based schema evolution
- **Environment Isolation**: Separate development/testing/production schemas
- **Backup Strategy**: Point-in-time recovery capabilities

### **Code Quality**
- **Type Hints**: Comprehensive type annotations throughout
- **Error Handling**: Explicit exception handling patterns
- **Logging**: Structured logging with appropriate detail levels
- **Configuration**: Environment-based settings with validation

### **Testing Strategy**
- **Integration Testing**: End-to-end pipeline validation
- **Unit Testing**: Component-level function testing
- **Performance Testing**: Baseline establishment and regression detection
- **Data Quality Testing**: Schema and relationship validation

## 🎯 **Commercial Objectives Alignment**

### **Business Context**
- **Purpose**: Commercial data extraction for client analytics products
- **Revenue Model**: Data capture and value-add services for client sales
- **Market Focus**: Saudi Arabian real estate market coverage
- **Product Goal**: Rich analytics and insights capabilities for clients

### **Technical Enablers**
- **Scalable Architecture**: Async patterns ready for production deployment
- **Data Quality**: High-integrity processing for reliable client products
- **Performance**: Efficient processing suitable for commercial operations
- **Maintenance**: Well-documented patterns for operational sustainability

### **Success Metrics**
- **Data Completeness**: Comprehensive parcel coverage across provinces
- **Processing Reliability**: High success rates for production confidence
- **Performance Efficiency**: Processing times suitable for commercial scale
- **Data Integrity**: Quality standards appropriate for client products

## 🔄 **Current Development Phase**

### **Immediate Focus: Baseline Validation**
- **Install Package**: Development environment setup with uv
- **Run Pipeline**: Execute 3x3 geometric processing
- **Validate Database**: Confirm schema population and relationships
- **Test Enrichment**: Verify API integration and data quality
- **Measure Performance**: Establish baseline metrics for scaling

### **Next Phase: Multi-Province Validation**
- **Second Province**: Test with different province data
- **Scale Testing**: Larger grid processing for performance validation
- **Conflict Testing**: Verify multi-province data isolation
- **Performance Tuning**: Optimize based on baseline measurements

### **Future Phase: Production Scale**
- **Full Province**: Complete Riyadh province processing
- **All Provinces**: Saudi Arabia-wide data extraction
- **Dynamic Discovery**: Automated boundary detection system
- **Commercial Deployment**: Client-ready data products

## 🆕 Province Sync & Schema Alignment
- Province data is always synced from the Suhail API before pipeline runs.
- The `parcels` table includes a nullable `region_id` (BIGINT) column.
- All schema changes are managed via Alembic migrations.
- For reproducibility, recommend DB reset + province sync + pipeline run in CI/CD.

This technical context reflects the actual current state: fresh database foundation, proven async architecture ready for validation, and systematic approach to building commercial-grade Saudi Arabian real estate data processing capabilities. 