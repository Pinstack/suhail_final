# Project Brief: Meshic Geospatial Data Pipeline

## Project Overview
Commercial geospatial data processing pipeline for capturing Saudi Arabian land parcel data from MVT tiles. Built to extract and enrich real estate data for client sales and analytics products.

## Current Status
- **Database**: Fresh PostgreSQL/PostGIS database (recently dropped and recreated)
- **Data State**: Empty - ready for baseline testing
- **Pipeline State**: Functional architecture with async processing capabilities
- **Testing Scope**: 3x3 tile grid in central Riyadh for validation

## Business Objective
Extract and process Saudi Arabian real estate data to build commercial analytics products for client sales. This is a data capture and value-add operation, not platform development for Suhail.

## Core Specifications

### **Current Testing Scale** 
- **Coverage**: Central Riyadh test region (3x3 tile grid = 9 tiles)
- **Purpose**: Validate pipeline architecture and database schema
- **Expected Volume**: ~1,000-2,000 parcels for initial testing
- **Geographic Area**: Small test area in central Riyadh

### **Production Scale Goals**
- **Phase 1**: Full Riyadh province (52x52 grid from previous testing showed 1M+ parcels)
- **Phase 2**: Test additional province to validate multi-province handling  
- **Phase 3**: All 6 Saudi provinces with dynamic boundary discovery
- **Future**: Dynamic boundary discovery system for automated extent detection

## Technical Requirements

1. **MVT Processing**: Decode Mapbox Vector Tiles to PostGIS geometries
2. **Database Schema**: Robust PostGIS schema as single source of truth
3. **Multi-Province Support**: Database must handle multiple provinces safely
4. **API Enrichment**: Integrate with Suhail APIs for transaction and zoning data
5. **Data Integrity**: Maintain referential integrity with proper foreign keys
6. **Chunked Processing**: Handle large datasets efficiently with batching

## Technical Constraints

- **Database**: PostgreSQL with PostGIS spatial extensions (recently reset)
- **API Endpoint**: api2.suhail.ai for enrichment data
- **Tile Server**: Province-specific tile servers (riyadh, eastern_region, etc.)
- **Processing**: Python/SQLAlchemy with async capabilities
- **Migration Tool**: Alembic for all database schema changes

## Current Phase: Baseline Validation

### **Immediate Goals**
1. ✅ **Fresh Database**: Recently reset with robust schema
2. 🔄 **3x3 Testing**: Validate basic pipeline with small grid
3. 🔄 **Multi-Province Test**: Ensure database handles multiple provinces
4. 🔄 **Full Province Test**: Scale to complete province processing
5. 🔄 **Dynamic Discovery**: Build boundary detection system

### **Success Criteria**
- 3x3 grid processes successfully and persists to database
- Second province test confirms no data conflicts
- Pipeline architecture ready for 1M+ parcel scale
- Database schema robust and performs well

## Future Development

### **Dynamic Boundary Discovery System** (To Be Built)
- **Requirement**: Discover province bbox extents using lower zoom levels
- **Process**: Admin boundary detection → bbox extraction → z15 tile generation
- **Benefit**: Eliminate manual coordinate management for province coverage
- **Timeline**: After baseline validation complete

## Deliverables

1. **Validated Pipeline**: 3x3 test grid working end-to-end
2. **Robust Database**: Multi-province capable schema
3. **Scalable Architecture**: Ready for 1M+ parcels
4. **Commercial Foundation**: Data capture system for client products 