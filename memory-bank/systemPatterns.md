# System Patterns and Architecture

## 🏗️ **Core Architecture: Functional Async Design**

### **Design Philosophy**
The Meshic pipeline uses **functional async patterns** rather than class-based OOP, optimized for high-performance geospatial data processing at scale.

### **Key Architectural Principles**
1. **Async-First**: All I/O operations use async/await patterns
2. **Functional Composition**: Functions compose rather than inherit
3. **Resource Efficiency**: Proper session and connection management
4. **Error Resilience**: Graceful failure handling with retry logic
5. **Database as Truth**: Schema-first design with type safety

## 🔄 **Pipeline Architecture Patterns**

### **1. Multi-Stage Processing Pipeline**

#### **Stage 1: Geometric Data Extraction**
```python
# Functional async pipeline pattern
async def geometric_pipeline():
    # Tile discovery and download
    tiles = await discover_tiles(province, zoom_level)
    downloaded = await download_tiles_concurrent(tiles, max_concurrent=5)
    
    # MVT decoding and spatial processing
    features = await decode_mvt_tiles(downloaded)
    geometries = await stitch_geometries(features)
    
    # Database persistence with type safety
    await persist_to_postgis(geometries, chunk_size=5000)
```

#### **Stage 2: Enrichment Data Integration**
```python
# Async batch processing pattern
async def enrichment_pipeline():
    parcel_ids = await get_unprocessed_parcel_ids(engine, limit=1000)
    
    async with aiohttp.ClientSession() as session:
        client = SuhailAPIClient(session)
        
        async for batch in process_batches(parcel_ids, batch_size=50):
            enrichment_data = await fetch_enrichment_batch(client, batch)
            await store_enrichment_data(enrichment_data)
```

### **2. Resource Management Patterns**

#### **Database Connection Pattern**
```python
# Singleton engine with async session management
engine = get_async_db_engine()  # Global singleton

async def database_operation():
    async with engine.begin() as conn:
        result = await conn.execute(query)
        return result
```

#### **HTTP Session Management**
```python
# Session lifecycle management
async with aiohttp.ClientSession(
    timeout=aiohttp.ClientTimeout(total=60),
    connector=aiohttp.TCPConnector(limit=20)
) as session:
    # All HTTP operations within session scope
    client = SuhailAPIClient(session)
    await client.fetch_data()
```

### **3. Error Handling Patterns**

#### **Graceful Degradation**
```python
async def fetch_with_retry(url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return await fetch_data(url)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts: {e}")
                return None
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

#### **Partial Success Handling**
```python
async def process_batch_with_partial_success(batch):
    results = []
    for item in batch:
        try:
            result = await process_item(item)
            results.append(result)
        except Exception as e:
            logger.warning(f"Item {item.id} failed: {e}")
            # Continue processing other items
    return results
```

## 🗄️ **Database Design Patterns**

### **1. Schema-First Design**
- **PostGIS Foundation**: Spatial extensions with EPSG:4326 coordinate system
- **Type Safety**: Proper data types aligned with MVT source data
- **Referential Integrity**: Foreign key relationships maintain data consistency
- **Performance Optimization**: Spatial indexes and optimized column types

### **2. Migration Management Pattern**
```python
# Alembic migrations for schema evolution
def upgrade():
    # Create tables with spatial extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    
    # Create core spatial tables
    op.create_table('parcels',
        sa.Column('id', sa.BigInteger(), primary_key=True),
        sa.Column('geometry', Geometry('MULTIPOLYGON', 4326)),
        sa.Column('shape_area', sa.Double()),
        sa.Column('province_id', sa.BigInteger(), sa.ForeignKey('provinces.id'))
    )
    
    # Create spatial indexes
    op.execute("CREATE INDEX idx_parcels_geom ON parcels USING GIST(geometry)")
```

### **3. Foreign Key Relationship Pattern**
```sql
-- Core reference tables
provinces (id, name_ar, name_en, geometry)
municipalities (id, name_ar, name_en, province_id, geometry)
zoning_rules (id, rule_name_ar, description)
land_use_groups (id, group_name_ar, category)

-- Spatial data tables with relationships
parcels (id, geometry, shape_area, province_id, municipality_id, zoning_id)
neighborhoods (id, geometry, name_ar, municipality_id)
subdivisions (id, geometry, name_ar, province_id)
```

## 🚀 **Performance Optimization Patterns**

### **1. Async Concurrency Control**
```python
# Controlled concurrency with semaphore
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent operations

async def controlled_fetch(url: str):
    async with semaphore:
        return await fetch_data(url)

# Batch processing with concurrency
async def process_concurrent_batches(items, batch_size=50):
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    
    tasks = [controlled_fetch(batch) for batch in batches]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### **2. Memory Management Pattern**
```python
# Generator pattern for large datasets
async def process_large_dataset(query):
    async with engine.stream(query) as result:
        async for row in result:
            yield process_row(row)
            # Memory released after each iteration

# Chunked database operations
async def bulk_insert_chunked(data, chunk_size=5000):
    for chunk in chunks(data, chunk_size):
        async with engine.begin() as conn:
            await conn.execute(insert_statement, chunk)
```

### **3. Caching and Optimization**
```python
# Connection pooling
engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=30,
    pool_recycle=3600
)

# Result caching for reference data
@lru_cache(maxsize=100)
async def get_province_by_name(name: str):
    # Cache frequently accessed reference data
    return await fetch_province(name)
```

## 🔧 **Configuration Management Patterns**

### **1. Environment-Based Configuration**
```yaml
# pipeline_config.yaml
database:
  host: ${DB_HOST:localhost}
  port: ${DB_PORT:5432}
  
processing:
  max_concurrent_downloads: ${MAX_CONCURRENT:5}
  batch_size: ${BATCH_SIZE:50}
  
provinces:
  riyadh:
    tile_server: "https://tiles.suhail.ai/maps/riyadh"
    zoom_level: 15
```

### **2. Validation Pattern**
```python
# Pydantic models for configuration validation
class ProcessingConfig(BaseModel):
    max_concurrent_downloads: int = Field(ge=1, le=20)
    batch_size: int = Field(ge=10, le=1000)
    chunk_size: int = Field(ge=100, le=10000)

class ProvinceConfig(BaseModel):
    tile_server: HttpUrl
    zoom_level: int = Field(ge=10, le=18)
    bbox: Optional[List[float]] = None
```

## 🏛️ **Service Layer Patterns**

### **1. Repository Pattern for Data Access**
```python
# Functional repository pattern
async def get_unprocessed_parcels(engine, limit: int = 1000):
    query = """
    SELECT id FROM parcels 
    WHERE enriched_at IS NULL 
    ORDER BY created_at 
    LIMIT :limit
    """
    async with engine.begin() as conn:
        result = await conn.execute(text(query), {"limit": limit})
        return [row.id for row in result]

async def store_enrichment_batch(session, batch_data):
    async with session.begin():
        for table_name, records in batch_data.items():
            await session.execute(insert_statement, records)
```

### **2. Service Composition Pattern**
```python
# Composable service functions
async def run_complete_pipeline(province: str, strategy: str = "optimal"):
    # Geometric processing
    tiles = await discover_province_tiles(province, strategy)
    spatial_data = await process_geometric_pipeline(tiles)
    
    # Enrichment processing
    parcel_ids = await extract_parcel_ids(spatial_data)
    enrichment_data = await process_enrichment_pipeline(parcel_ids)
    
    return {
        "spatial_records": len(spatial_data),
        "enriched_records": len(enrichment_data)
    }
```

## 🔍 **Monitoring and Observability Patterns**

### **1. Structured Logging Pattern**
```python
import structlog

logger = structlog.get_logger()

async def process_province(province_name: str):
    logger.info("province_processing_started", 
                province=province_name, 
                timestamp=datetime.utcnow())
    
    try:
        result = await process_data(province_name)
        logger.info("province_processing_completed",
                   province=province_name,
                   records_processed=len(result))
        return result
    except Exception as e:
        logger.error("province_processing_failed",
                    province=province_name,
                    error=str(e))
        raise
```

### **2. Metrics Collection Pattern**
```python
# Performance metrics collection
class PipelineMetrics:
    def __init__(self):
        self.start_time = None
        self.records_processed = 0
        self.errors_count = 0
    
    async def track_operation(self, operation_name: str):
        start = time.time()
        try:
            yield
            duration = time.time() - start
            logger.info("operation_completed",
                       operation=operation_name,
                       duration_seconds=duration)
        except Exception as e:
            self.errors_count += 1
            logger.error("operation_failed",
                        operation=operation_name,
                        error=str(e))
            raise
```

## 🧪 **Testing Patterns**

### **1. Database Testing Pattern**
```python
# Transaction rollback testing
@pytest.fixture
async def test_db_session():
    async with engine.begin() as conn:
        async with conn.begin_nested() as trans:
            yield conn
            await trans.rollback()

async def test_parcel_insertion(test_db_session):
    # Test runs in transaction that gets rolled back
    await insert_test_parcel(test_db_session)
    result = await query_parcels(test_db_session)
    assert len(result) == 1
```

### **2. Mock API Testing Pattern**
```python
# Mock external API responses
@pytest.fixture
def mock_suhail_api():
    with aioresponses() as m:
        m.get(
            "https://api2.suhail.ai/transactions/12345",
            payload={"price": 1500000, "date": "2023-01-01"}
        )
        yield m

async def test_enrichment_pipeline(mock_suhail_api):
    result = await enrich_parcel("12345")
    assert result.price == 1500000
```

## 🎯 **Current Architecture Status**

### **Foundation Components: READY**
- ✅ **Database Schema**: Fresh PostGIS design with proper relationships
- ✅ **Async Pipeline**: Functional components ready for validation
- ✅ **Configuration**: Province-specific settings configured
- ✅ **CLI Interface**: Unified command system implemented

### **Testing Requirements: DEFINED**
- **3x3 Baseline**: Validate core pipeline with 9 tiles
- **Multi-Province**: Confirm architecture scales across provinces  
- **Performance**: Establish baseline metrics for production scaling
- **Data Quality**: Verify schema alignment and relationship integrity

### **Production Patterns: IMPLEMENTED**
- **Error Handling**: Comprehensive exception management
- **Resource Management**: Proper async session and connection handling
- **Performance Optimization**: Chunked processing and concurrency control
- **Monitoring**: Structured logging and metrics collection ready

This system architecture reflects the actual current implementation: functional async design, fresh database foundation, and systematic validation approach for commercial Saudi Arabia real estate data processing. 