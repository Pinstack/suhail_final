# Product Context: Suhail Geospatial Pipeline

## Vision
Scalable geospatial data processing pipeline for Riyadh real estate parcels, currently operating at development scale with plans for metropolitan area expansion.

## Problem Statement
- **Current State**: Manual, disconnected processing of geospatial parcel data
- **Challenge**: Need efficient automated pipeline for MVT tiles and API enrichment
- **Scale**: Starting with central Riyadh test region (9K parcels), preparing for city-wide expansion

## Solution Overview

### **Current Implementation**
- **Development Scale**: 3x3 tile grid covering central Riyadh test area
- **Data Processing**: 9,007 parcels with complete spatial and attribute data
- **Integration**: API enrichment for transactions, zoning, and price metrics
- **Architecture**: Two-stage pipeline (geometric + enrichment)

### **Target State**
- **Production Scale**: Expanded coverage across Riyadh metropolitan area
- **Enhanced Processing**: Larger tile grids with optimized performance
- **Comprehensive Data**: Full city coverage with all enrichment sources

## How It Should Work

### **User Experience Goals**
1. **Simplified Operation**: Single CLI commands for entire workflows
2. **Real-time Monitoring**: Status tracking and automated recommendations
3. **Flexible Strategies**: Multiple enrichment approaches for different needs
4. **Reliable Processing**: Robust error handling and recovery mechanisms

### **Technical Experience Goals**
1. **Performance**: Sub-second spatial queries regardless of scale
2. **Scalability**: Linear scaling from 9K to city-wide parcel coverage
3. **Maintainability**: Clear modular architecture with proper abstractions
4. **Observability**: Comprehensive logging and monitoring integration

## Success Metrics

### **Development Phase (Current)**
- ✅ **Data Coverage**: 9,007 parcels successfully processed
- ✅ **Quality**: 100% data completeness for current scope
- ✅ **Integration**: 5 enrichment strategies operational
- ✅ **Performance**: Sub-second queries on current dataset

### **Production Phase (Future)**
- 🎯 **Scale**: Expanded to full metropolitan area
- 🎯 **Performance**: Maintained sub-second query times at scale
- 🎯 **Reliability**: 99.9% uptime for processing operations
- 🎯 **Efficiency**: Optimized resource usage for larger datasets

## Business Value

### **Current Value**
- **Proof of Concept**: Validated technical approach with real data
- **Foundation**: Established architecture for future scaling
- **Integration**: Working API connections and data enrichment
- **Quality**: Proper referential integrity and spatial accuracy

### **Future Value**
- **Scale Economics**: Automated processing for entire city
- **Data Insights**: Comprehensive real estate analytics
- **Decision Support**: Enriched spatial data for planning
- **Operational Efficiency**: Reduced manual processing overhead

## 🆕 Province Sync & Schema Alignment
- Province data is always synced from the Suhail API before pipeline runs.
- The `parcels` table includes a nullable `region_id` (BIGINT) column.
- All schema changes are managed via Alembic migrations.
- For reproducibility, recommend DB reset + province sync + pipeline run in CI/CD.