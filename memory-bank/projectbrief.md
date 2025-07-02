# Project Brief: Suhail Geospatial Data Pipeline

## Project Overview
The Suhail Final project is a sophisticated **two-stage geospatial data processing pipeline** designed for the Saudi real estate markets.

## Core Requirements

### Stage 1: Geometric Pipeline
- Download and process geospatial shapes from Mapbox Vector Tiles (MVT)
- Source: `https://tiles.suhail.ai/maps/riyadh/{z}/{x}/{y}.vector.pbf`
- Coverage: Riyadh metropolitan area (15 layers, 1M+ parcels)
- Output: PostGIS database with geometric features

### Stage 2: Enrichment Pipeline
- Fetch business intelligence data from external APIs
- Transaction data: Historical real estate transactions
- Building rules: Zoning and construction regulations
- Price metrics: Market analysis and pricing trends
- Smart processing with multiple enrichment strategies

## Key Goals
1. **Performance**: High-speed asynchronous processing with 200+ concurrent connections
2. **Efficiency**: 93.3% efficiency gain by only processing parcels with `transaction_price > 0`
3. **Data Integrity**: Robust schema with foreign keys and referential integrity
4. **Operational Excellence**: Comprehensive monitoring, CLI tools, and automated workflows
5. **Scalability**: Handle 1M+ parcels with sub-second spatial queries

## Success Metrics
- **Parcels**: 1,032,380 land parcels with geometric boundaries
- **Transactions**: 45,526+ real estate transactions with enrichment data
- **Building Rules**: 68,396+ zoning and construction regulations
- **Price Metrics**: 752,963+ market analysis data points
- **Processing Speed**: 1,000+ parcels/minute with optimized settings

## Technology Stack
- **Backend**: Python 3.9+, SQLAlchemy, Alembic
- **Database**: PostgreSQL with PostGIS extension
- **Geospatial**: GeoPandas, MVT tiles processing
- **Async**: aiohttp for concurrent API processing
- **CLI**: Multiple command-line interfaces for operations

## Project Phases
- ✅ Phase 1: Codebase restructuring and refactoring (COMPLETED)
- ✅ Phase 2: Database schema and data integrity (COMPLETED)
- ✅ Phase 2B: Pipeline source-level data type fixes (COMPLETED)
- ✅ Delta Enrichment: MVT-based change detection (COMPLETED)
- 🔄 Phase 2C: Standardize naming conventions (FUTURE) 