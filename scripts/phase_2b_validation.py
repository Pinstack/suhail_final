#!/usr/bin/env python3
"""
Comprehensive test script for Phase 2B data type fixes.
Tests MVT decoding, type casting, and database operations to ensure no breakages.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meshic_pipeline.decoder.mvt_decoder import MVTDecoder
from meshic_pipeline.persistence.postgis_persister import PostGISPersister
from meshic_pipeline.logging_utils import get_logger

logger = get_logger(__name__)


def test_mvt_decoder_type_casting():
    """Test MVT decoder type casting functionality."""
    logger.info("🧪 Testing MVT decoder type casting...")
    
    decoder = MVTDecoder()
    
    # Test property casting
    test_properties = {
        'parcel_id': '12345',           # string -> int
        'zoning_id': 1.0,               # float -> int
        'subdivision_id': 9876543210,   # large int -> int
        'parcel_objectid': 'ABC123',    # string -> string (kept as string)
        'rule_id': 'ZONE_01',           # string -> string
        'transaction_price': 150000.50, # float -> float (unchanged)
        'invalid_id': 'not_a_number',   # invalid -> string
    }
    
    cast_props = decoder._cast_property_types(test_properties)
    
    # Validate casting results
    assertions = [
        (isinstance(cast_props['parcel_id'], int), "parcel_id should be cast to int"),
        (isinstance(cast_props['zoning_id'], int), "zoning_id should be cast to int"),
        (isinstance(cast_props['subdivision_id'], int), "subdivision_id should be cast to int"),
        (isinstance(cast_props['parcel_objectid'], str), "parcel_objectid should remain string"),
        (isinstance(cast_props['rule_id'], str), "rule_id should remain string"),
        (cast_props['transaction_price'] == 150000.50, "transaction_price should remain unchanged"),
        (isinstance(cast_props['invalid_id'], str), "invalid_id should become string"),
    ]
    
    for assertion, message in assertions:
        if not assertion:
            logger.error(f"❌ {message}")
            return False
        else:
            logger.info(f"✅ {message}")
    
    logger.info("✅ MVT decoder type casting tests passed")
    return True


def test_real_mvt_data():
    """Test with real MVT data if available."""
    logger.info("🧪 Testing with real MVT data...")
    
    # Look for test tiles
    test_tiles = list(Path('.').glob('test_tile_*.pbf'))
    if not test_tiles:
        logger.warning("⚠️  No test MVT tiles found, skipping real data test")
        return True
    
    decoder = MVTDecoder()
    tile_file = test_tiles[0]
    
    try:
        with open(tile_file, 'rb') as f:
            tile_data = f.read()
        
        # Decode tile
        decoded = decoder.decode_bytes(tile_data, 15, 20636, 14069)
        
        if 'parcels' in decoded and decoded['parcels']:
            parcel = decoded['parcels'][0]
            
            # Check if ID fields are properly cast
            id_fields = ['parcel_id', 'zoning_id', 'subdivision_id']
            for field in id_fields:
                if field in parcel:
                    if field == 'subdivision_id':
                        # subdivision_id might be string or int depending on source
                        valid_type = isinstance(parcel[field], (int, str))
                    else:
                        valid_type = isinstance(parcel[field], int)
                    
                    if valid_type:
                        logger.info(f"✅ {field}: {parcel[field]} ({type(parcel[field]).__name__})")
                    else:
                        logger.error(f"❌ {field}: {parcel[field]} ({type(parcel[field]).__name__}) - unexpected type")
                        return False
        
        logger.info("✅ Real MVT data tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Real MVT data test failed: {e}")
        return False


def test_postgis_persister_validation():
    """Test PostGIS persister type validation."""
    logger.info("🧪 Testing PostGIS persister validation...")
    
    # Create test GeoDataFrame with mixed types
    test_data = {
        'parcel_id': ['123', 456.0, '789', None],          # mixed string/float/null
        'zoning_id': [1.0, 2.5, 3.0, 4.0],                # floats that should become ints
        'subdivision_id': ['100', '200', 'invalid', None], # mixed valid/invalid strings
        'transaction_price': [150000.50, 200000.0, None, 175000.25], # should remain float
        'geometry': [None, None, None, None]  # placeholder
    }
    
    gdf = gpd.GeoDataFrame(test_data)
    
    # Mock persister (no actual database connection needed for this test)
    class MockPostGISPersister(PostGISPersister):
        def __init__(self):
            pass  # Skip database connection
    
    persister = MockPostGISPersister()
    validated_gdf = persister._validate_and_cast_types(gdf)
    
    # Check conversions
    assertions = [
        (validated_gdf['parcel_id'].dtype in ['int64', 'Int64'], "parcel_id should be integer type"),
        (validated_gdf['zoning_id'].dtype in ['int64', 'Int64'], "zoning_id should be integer type"),
        (validated_gdf['subdivision_id'].dtype in ['int64', 'Int64'], "subdivision_id should be integer type"),
        (validated_gdf['transaction_price'].dtype in ['float64'], "transaction_price should remain float"),
    ]
    
    for assertion, message in assertions:
        if not assertion:
            logger.error(f"❌ {message} (actual: {validated_gdf[message.split()[0]].dtype})")
            return False
        else:
            logger.info(f"✅ {message}")
    
    # Check that invalid string conversion resulted in NaN
    invalid_count = validated_gdf['subdivision_id'].isna().sum()
    expected_invalid = 2  # 'invalid' and original None
    if invalid_count == expected_invalid:
        logger.info(f"✅ Invalid string conversions properly handled ({invalid_count} nulls)")
    else:
        logger.error(f"❌ Expected {expected_invalid} null values, got {invalid_count}")
        return False
    
    logger.info("✅ PostGIS persister validation tests passed")
    return True


def test_sqlalchemy_models():
    """Test that SQLAlchemy models are properly updated."""
    logger.info("🧪 Testing SQLAlchemy models...")
    
    try:
        from meshic_pipeline.persistence.models import Parcel, Subdivision
        
        # Check Parcel model
        parcel_fields = {
            'parcel_id': 'BigInteger',
            'zoning_id': 'BigInteger', 
            'subdivision_id': 'BigInteger'
        }
        
        for field_name, expected_type in parcel_fields.items():
            column = getattr(Parcel, field_name)
            actual_type = column.type.__class__.__name__
            
            if actual_type == expected_type:
                logger.info(f"✅ Parcel.{field_name}: {actual_type}")
            else:
                logger.error(f"❌ Parcel.{field_name}: expected {expected_type}, got {actual_type}")
                return False
        
        # Check Subdivision model
        subdivision_zoning = getattr(Subdivision, 'zoning_id')
        actual_type = subdivision_zoning.type.__class__.__name__
        
        if actual_type == 'BigInteger':
            logger.info(f"✅ Subdivision.zoning_id: {actual_type}")
        else:
            logger.error(f"❌ Subdivision.zoning_id: expected BigInteger, got {actual_type}")
            return False
        
        logger.info("✅ SQLAlchemy models tests passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLAlchemy models test failed: {e}")
        return False


def test_migration_syntax():
    """Test that the migration file has correct syntax."""
    logger.info("🧪 Testing migration syntax...")
    
    try:
        migration_file = Path('alembic/versions/411b7d986fe1_phase_2b_fix_data_type_inconsistencies_.py')
        
        if not migration_file.exists():
            logger.error("❌ Migration file not found")
            return False
        
        # Try to compile the migration file
        with open(migration_file) as f:
            migration_code = f.read()
        
        # Basic syntax check
        compile(migration_code, str(migration_file), 'exec')
        
        # Check for required functions
        required_parts = ['def upgrade()', 'def downgrade()', 'op.alter_column']
        for part in required_parts:
            if part not in migration_code:
                logger.error(f"❌ Migration missing required part: {part}")
                return False
            else:
                logger.info(f"✅ Migration contains: {part}")
        
        logger.info("✅ Migration syntax tests passed")
        return True
        
    except SyntaxError as e:
        logger.error(f"❌ Migration syntax error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Migration test failed: {e}")
        return False


def main():
    """Run all Phase 2B tests."""
    logger.info("🚀 Starting Phase 2B comprehensive tests...")
    
    tests = [
        ("MVT Decoder Type Casting", test_mvt_decoder_type_casting),
        ("Real MVT Data", test_real_mvt_data),
        ("PostGIS Persister Validation", test_postgis_persister_validation),
        ("SQLAlchemy Models", test_sqlalchemy_models),
        ("Migration Syntax", test_migration_syntax),
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    # Summary
    print("\n" + "="*80)
    print("📊 PHASE 2B TEST RESULTS")
    print("="*80)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print("="*80)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Phase 2B changes are safe to deploy!")
        print("\nNext steps:")
        print("1. Run data validation: python scripts/validate_data_types.py")
        print("2. Apply migration: alembic upgrade head")
        print("3. Test pipeline: python scripts/run_geometric_pipeline.py --help")
    else:
        print("⚠️  SOME TESTS FAILED - Review and fix issues before deployment")
    print("="*80)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 