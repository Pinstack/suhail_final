# Product Context: Suhail Geospatial Pipeline

## Vision
Scalable geospatial data processing pipeline for all Saudi provinces, now operating with a database-driven tile discovery and orchestration system.

## Problem Statement
- **Previous State**: Manual, disconnected processing of geospatial parcel data
- **Current State**: Automated, DB-driven pipeline for MVT tiles and API enrichment
- **Scale**: Ready for province-wide and all-Saudi scrapes

## Solution Overview

### **Current Implementation**
- **DB-Driven Tile Discovery**: All tiles to be processed are stored in the `tile_urls` table, supporting resumable, province-wide, and all-Saudi scrapes.
- **Data Processing**: 9,007 parcels with complete spatial and attribute data (baseline); ready for full-scale runs
- **Integration**: API enrichment for transactions, zoning, and price metrics
- **Architecture**: Two-stage pipeline (geometric + enrichment), now orchestrated from the database

### **Target State**
- **Production Scale**: Expanded coverage across all Saudi provinces
- **Enhanced Processing**: Large tile grids with optimized, resumable performance
- **Comprehensive Data**: Full country coverage with all enrichment sources

## How It Should Work

### **User Experience Goals**
1. **Simplified Operation**: Single CLI commands for entire workflows
2. **Real-time Monitoring**: Status tracking and automated recommendations
3. **Flexible Strategies**: Multiple enrichment approaches for different needs
4. **Reliable Processing**: Robust error handling and recovery mechanisms
5. **Resumability**: Pipeline can be stopped and resumed, processing only pending/failed tiles

### **Technical Experience Goals**
1. **Performance**: Sub-second spatial queries regardless of scale
2. **Scalability**: Linear scaling from 9K to all-province parcel coverage
3. **Maintainability**: Clear modular architecture with proper abstractions
4. **Observability**: Comprehensive logging and monitoring integration
5. **DB-Driven Orchestration**: All tile discovery and processing is managed via the database

## Success Metrics

### **Development Phase (Current)**
- 	**Data Coverage**: 9,007 parcels successfully processed (baseline)
- 	**Quality**: 100% data completeness for current scope
- 	**Integration**: 5 enrichment strategies operational
- 	**Performance**: Sub-second queries on current dataset

### **Production Phase (Future)**
- 	**Scale**: Expanded to all Saudi provinces
- 	**Performance**: Maintained sub-second query times at scale
- 	**Reliability**: 99.9% uptime for processing operations
- 	**Efficiency**: Optimized resource usage for larger datasets

## Business Value

### **Current Value**
- **Proof of Concept**: Validated technical approach with real data
- **Foundation**: Established architecture for future scaling
- **Integration**: Working API connections and data enrichment
- **Quality**: Proper referential integrity and spatial accuracy

### **Future Value**
- **Scale Economics**: Automated processing for entire country
- **Data Insights**: Comprehensive real estate analytics
- **Decision Support**: Enriched spatial data for planning
- **Operational Efficiency**: Reduced manual processing overhead

## 🆕 Province Sync & Schema Alignment
- Province data is always synced from the Suhail API before pipeline runs.
- The `parcels` table includes a nullable `region_id` (BIGINT) column.
- All schema changes are managed via Alembic migrations.
- For reproducibility, recommend DB reset + province sync + pipeline run in CI/CD.