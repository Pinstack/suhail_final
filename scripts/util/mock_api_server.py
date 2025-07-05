#!/usr/bin/env python3
"""
Mock API server for testing Suhail enrichment pipeline.
Run with: python scripts/mock_api_server.py
Then set SUHAIL_API_BASE_URL=http://localhost:8000 in .env
"""

from fastapi import FastAPI, Query
from typing import List
import uvicorn
from datetime import datetime

app = FastAPI(title="Mock Suhail API", version="1.0.0")

@app.get("/buildingRules")
async def get_building_rules(parcelObjectId: str = Query(...)):
    """Mock building rules endpoint"""
    return {
        "status": True,
        "data": [
            {
                "ruleId": f"RULE_{parcelObjectId[:6]}",
                "zoningId": "RES001",
                "zoningColor": "#00FF00",
                "zoningGroup": "Residential",
                "landuse": "Residential Low Density",
                "description": "Standard residential zoning",
                "name": "Residential Zone R1",
                "coloring": "Green",
                "coloringDescription": "Green residential zone",
                "maxBuildingCoefficient": 0.6,
                "maxBuildingHeight": 15.0,
                "maxParcelCoverage": 0.4,
                "maxRuleDepth": 25.0,
                "mainStreetsSetback": 5.0,
                "secondaryStreetsSetback": 3.0,
                "sideRearSetback": 2.0
            }
        ]
    }

@app.get("/priceMetrics")
async def get_price_metrics(parcelObjsIds: List[str] = Query(...), groupingType: str = Query("Monthly")):
    """Mock price metrics endpoint"""
    metrics_data = []
    for parcel_id in parcelObjsIds:
        metrics_data.append({
            "parcelObjId": parcel_id,
            "parcelMetrics": [
                {
                    "month": 12,
                    "year": 2023,
                    "metricsType": "AVERAGE",
                    "avaragePriceOfMeter": 2500.0
                },
                {
                    "month": 11,
                    "year": 2023,
                    "metricsType": "AVERAGE", 
                    "avaragePriceOfMeter": 2450.0
                }
            ]
        })
    
    return {
        "status": True,
        "data": metrics_data
    }

@app.get("/transactions")
async def get_transactions(parcelObjectId: str = Query(...)):
    """Mock transactions endpoint"""
    return {
        "status": True,
        "data": {
            "transactions": [
                {
                    "transactionNumber": f"TX_{parcelObjectId[:8]}",
                    "transactionPrice": 500000.0,
                    "priceOfMeter": 2000.0,
                    "transactionDate": "2023-11-15T00:00:00Z",
                    "area": 250.0
                }
            ]
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Mock Suhail API Server on http://localhost:8000")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🏥 Health Check: http://localhost:8000/health")
    uvicorn.run(app, host="0.0.0.0", port=8000) 
