# Product Context: Suhail Geospatial Data Pipeline

## Why This Project Exists

The Suhail pipeline addresses critical needs in the Riyadh real estate market by providing comprehensive, accurate, and timely geospatial data processing for over 1 million land parcels.

## Problems It Solves

### 1. **Data Integration Challenge**
- **Problem**: Fragmented real estate data across multiple sources
- **Solution**: Unified pipeline combining geometric data (MVT tiles) with business intelligence (APIs)

### 2. **Scale and Performance**
- **Problem**: Processing 1M+ parcels efficiently
- **Solution**: Two-stage architecture with intelligent parcel selection (93.3% efficiency gain)

### 3. **Data Freshness and Accuracy**
- **Problem**: Keeping transaction data current and complete
- **Solution**: Multiple enrichment strategies including delta detection and incremental updates

### 4. **Operational Complexity**
- **Problem**: Complex data pipelines requiring manual intervention
- **Solution**: Automated monitoring, smart recommendations, and comprehensive CLI tools

## How It Should Work

### **Geometric Pipeline (Stage 1)**
1. Download MVT tiles for Riyadh metropolitan area
2. Process 15 different layers (parcels, neighborhoods, subdivisions, etc.)
3. Stitch tile boundaries and validate geometries
4. Store in PostGIS with spatial indexes
5. **Key Insight**: Reveals parcels with `transaction_price > 0` for efficient enrichment

### **Enrichment Pipeline (Stage 2)**
1. **Smart Selection**: Only process parcels that need enrichment
2. **Concurrent Processing**: 200+ API connections for maximum throughput
3. **Multiple Strategies**:
   - **Delta Enrichment**: MVT-based change detection (most precise)
   - **Trigger-Based**: Process parcels with `transaction_price > 0` (maximum efficiency)
   - **Incremental**: Time-based updates for new transactions
   - **Full Refresh**: Complete data validation (quarterly)

### **Monitoring and Operations**
1. Real-time status tracking
2. Automated scheduling recommendations
3. Performance metrics and optimization
4. Data integrity validation