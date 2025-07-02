# Tech Context: Suhail Geospatial Data Pipeline

## Core Technologies

### **Python Ecosystem**
- **Version**: Python 3.9+
- **Package Management**: pip with `pyproject.toml`
- **Virtual Environment**: `.venv` for isolation

### **Database Stack**
- **Primary**: PostgreSQL with PostGIS extension
- **ORM**: SQLAlchemy with GeoAlchemy2 for spatial types
- **Migrations**: Alembic for schema versioning
- **Connection**: psycopg2 with connection pooling

### **Geospatial Processing**
- **Core Library**: GeoPandas for spatial data manipulation
- **Tile Format**: Mapbox Vector Tiles (MVT/PBF)
- **Coordinate System**: EPSG:4326 (WGS84)
- **Spatial Operations**: PostGIS functions and GIST indexing

### **Async and HTTP**
- **HTTP Client**: aiohttp for async API calls
- **Concurrency**: asyncio with semaphore-based limiting
- **Session Management**: Connection pooling and reuse

## Development Setup

### **Directory Structure**
```
Suhail_Final/
├── src/meshic_pipeline/     # Main application code
├── scripts/                 # Operational scripts
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── memory-bank/             # Project documentation
├── .env                     # Environment configuration
├── pipeline_config.yaml     # Pipeline grid configuration
└── pyproject.toml          # Python project configuration
```

### **Configuration Management**
- **Settings**: Pydantic-based configuration with environment variables
- **Database URL**: `postgresql://username:password@localhost:5432/meshic`
- **API Base URL**: `https://api2.suhail.ai`
- **Environment Files**: `.env` for local development

### **Entry Points**
```bash
# Geometric pipeline
meshic-pipeline geometric
python scripts/run_geometric_pipeline.py

# Enrichment pipeline
meshic-pipeline enrich [strategy]
python scripts/run_enrichment_pipeline.py [command]

# Monitoring
python scripts/run_monitoring.py [command]
```

## Technical Constraints

### **Performance Requirements**
- **Memory**: 8GB+ RAM recommended for large-scale processing
- **Concurrency**: 200+ simultaneous API connections
- **Throughput**: 1,000+ parcels/minute processing target
- **Database**: Handle 1M+ spatial records with sub-second queries

### **Data Volume Constraints**
- **Parcels**: 1,032,380 land parcels
- **Transactions**: 45,526+ historical records
- **Grid Coverage**: 52x52 tile grid at zoom level 15
- **Geographic Scope**: Complete Riyadh metropolitan area

### **API Limitations**
- **Rate Limiting**: Managed through configurable delays
- **Timeout Handling**: 60-second default with retries
- **Error Recovery**: Exponential backoff with max attempts

## Dependencies

### **Core Dependencies**
```toml
geopandas = "^0.14.0"          # Geospatial data processing
sqlalchemy = "^2.0.0"          # Database ORM
alembic = "^1.12.0"           # Database migrations
aiohttp = "^3.9.0"            # Async HTTP client
pydantic = "^2.4.0"           # Configuration management
pydantic-settings = "^2.0.0"   # Environment-based settings
```

### **Geospatial Dependencies**
```toml
geoalchemy2 = "^0.14.0"       # SQLAlchemy spatial types
fiona = "^1.9.0"              # Spatial file I/O
shapely = "^2.0.0"            # Geometric operations
pyproj = "^3.6.0"             # Coordinate transformations
```

### **Development Dependencies**
```toml
pytest = "^7.4.0"             # Testing framework
black = "^23.0.0"             # Code formatting
isort = "^5.12.0"             # Import sorting
mypy = "^1.6.0"               # Type checking
```

## Database Schema

### **Migration System**
- **Tool**: Alembic with autogenerate capability
- **Strategy**: Incremental migrations with rollback support
- **Naming**: Descriptive migration names with phase indicators

### **Key Tables**
```sql
-- Core spatial data
parcels (1M+ records with geometry)
neighborhoods (administrative boundaries)
provinces (regional boundaries)

-- Business data
transactions (45K+ historical records)
building_rules (68K+ zoning regulations)
parcel_price_metrics (752K+ market analysis)

-- Lookup tables
municipalities, subdivisions, land_use_groups
```

### **Constraints and Indexes**
- **Primary Keys**: All core tables have proper PKs
- **Foreign Keys**: 9 relationships for referential integrity
- **Spatial Indexes**: GIST indexes on all geometry columns
- **Unique Constraints**: Prevent duplicate enrichment data

## Development Workflow

### **Code Organization**
- **Modular Design**: Clear separation of concerns
- **Type Hints**: Comprehensive typing throughout
- **Configuration**: Environment-driven settings
- **Error Handling**: Graceful degradation patterns

### **Testing Strategy**
- **Unit Tests**: Component-level validation
- **Integration Tests**: End-to-end pipeline testing
- **Data Validation**: Type conversion and schema compliance
- **Performance Tests**: Memory and timing validation

### **Deployment Considerations**
- **Environment Variables**: Database URL, API endpoints
- **Resource Requirements**: Memory and CPU specifications
- **Monitoring**: Built-in performance tracking
- **Scaling**: Configurable concurrency and batch sizes 