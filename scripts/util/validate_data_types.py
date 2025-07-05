#!/usr/bin/env python3
"""
Data type validation script for Phase 2B.
Checks if existing data can be safely converted from current types to target types.
"""

import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from meshic_pipeline.logging_utils import get_logger

logger = get_logger(__name__)


def validate_integer_conversion(engine, table_name: str, column_name: str, current_type: str) -> dict:
    """Validate if a column can be safely converted to BigInteger."""
    result = {
        "table": table_name,
        "column": column_name,
        "current_type": current_type,
        "can_convert": False,
        "null_count": 0,
        "total_count": 0,
        "invalid_values": [],
        "sample_values": [],
        "recommendations": []
    }
    
    try:
        with engine.connect() as conn:
            # Get basic stats
            count_query = f'SELECT COUNT(*) as total, COUNT("{column_name}") as non_null FROM "{table_name}"'
            stats = conn.execute(text(count_query)).fetchone()
            result["total_count"] = stats.total
            result["null_count"] = stats.total - stats.non_null
            
            # Get sample values
            sample_query = f'SELECT "{column_name}" FROM "{table_name}" WHERE "{column_name}" IS NOT NULL LIMIT 10'
            samples = conn.execute(text(sample_query)).fetchall()
            result["sample_values"] = [row[0] for row in samples]
            
            if current_type.upper() in ['DOUBLE PRECISION', 'REAL']:
                # Check for non-integer values in float columns
                fractional_query = f'''
                SELECT "{column_name}" 
                FROM "{table_name}" 
                WHERE "{column_name}" IS NOT NULL 
                AND "{column_name}" != FLOOR("{column_name}")
                LIMIT 5
                '''
                fractional = conn.execute(text(fractional_query)).fetchall()
                if fractional:
                    result["invalid_values"] = [row[0] for row in fractional]
                    result["recommendations"].append(f"Contains {len(fractional)} fractional values - consider ROUND() or FLOOR() in migration")
                else:
                    result["can_convert"] = True
                    result["recommendations"].append("All values are integers - safe to convert")
                    
            elif current_type.upper() in ['CHARACTER VARYING', 'TEXT']:
                # Check if string values can be converted to integers
                invalid_query = f'''
                SELECT "{column_name}" 
                FROM "{table_name}" 
                WHERE "{column_name}" IS NOT NULL 
                AND TRIM("{column_name}") !~ '^-?[0-9]+$'
                LIMIT 5
                '''
                invalid = conn.execute(text(invalid_query)).fetchall()
                if invalid:
                    result["invalid_values"] = [row[0] for row in invalid]
                    result["recommendations"].append(f"Contains non-numeric strings - data cleaning required")
                else:
                    # Check for values that would overflow BigInteger
                    overflow_query = f'''
                    SELECT "{column_name}" 
                    FROM "{table_name}" 
                    WHERE "{column_name}" IS NOT NULL 
                    AND (CAST("{column_name}" AS NUMERIC) > 9223372036854775807 
                         OR CAST("{column_name}" AS NUMERIC) < -9223372036854775808)
                    LIMIT 5
                    '''
                    overflow = conn.execute(text(overflow_query)).fetchall()
                    if overflow:
                        result["invalid_values"] = [row[0] for row in overflow]
                        result["recommendations"].append("Values would overflow BigInteger - consider using NUMERIC type")
                    else:
                        result["can_convert"] = True
                        result["recommendations"].append("All string values are valid integers - safe to convert")
            else:
                result["can_convert"] = True
                result["recommendations"].append(f"Type {current_type} should be compatible")
                
    except Exception as e:
        result["recommendations"].append(f"Error during validation: {e}")
        logger.error(f"Error validating {table_name}.{column_name}: {e}")
    
    return result


def main():
    """Main validation function."""
    logger.info("🔍 Starting Phase 2B data type validation...")
    
    # Database connection
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return False
    
    try:
        engine = create_engine(database_url)
        
        # Define columns to validate (from Phase 2B TODO)
        validations = [
            ("parcels", "parcel_id", "double precision"),
            ("parcels", "zoning_id", "double precision"), 
            ("parcels", "subdivision_id", "character varying"),
            ("subdivisions", "zoning_id", "double precision"),
        ]
        
        results = []
        all_safe = True
        
        for table, column, current_type in validations:
            logger.info(f"Validating {table}.{column} ({current_type} -> BigInteger)")
            result = validate_integer_conversion(engine, table, column, current_type)
            results.append(result)
            
            if not result["can_convert"]:
                all_safe = False
        
        # Report results
        print("\n" + "="*80)
        print("📊 DATA TYPE VALIDATION REPORT")
        print("="*80)
        
        for result in results:
            status = "✅ SAFE" if result["can_convert"] else "⚠️  ISSUES"
            print(f"\n{status} {result['table']}.{result['column']}")
            print(f"  Current Type: {result['current_type']}")
            print(f"  Total Records: {result['total_count']:,}")
            print(f"  Null Records: {result['null_count']:,}")
            
            if result["sample_values"]:
                print(f"  Sample Values: {result['sample_values'][:5]}")
            
            if result["invalid_values"]:
                print(f"  ❌ Invalid Values: {result['invalid_values']}")
            
            for rec in result["recommendations"]:
                print(f"  💡 {rec}")
        
        print("\n" + "="*80)
        if all_safe:
            print("✅ ALL VALIDATIONS PASSED - Safe to proceed with migration")
        else:
            print("⚠️  VALIDATION ISSUES FOUND - Review and fix data before migration")
        print("="*80)
        
        return all_safe
        
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
