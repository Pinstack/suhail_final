import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlalchemy
from src.meshic_pipeline.config import settings

def main():
    """
    Checks for and resolves orphaned rows before applying foreign key constraints.
    Sets the foreign key column to NULL if the referenced key does not exist.
    """
    print("Script starting: Validating data for foreign key constraints...")
    
    fk_relationships = [
        # (table, fk_column, parent_table, parent_pk_column)
        ('transactions', 'parcel_objectid', 'parcels', 'parcel_objectid'),
        ('parcel_price_metrics', 'parcel_objectid', 'parcels', 'parcel_objectid'),
        ('parcel_price_metrics', 'neighborhood_id', 'neighborhoods', 'neighborhood_id'),
        ('building_rules', 'parcel_objectid', 'parcels', 'parcel_objectid'),
        ('parcels', 'neighborhood_id', 'neighborhoods', 'neighborhood_id'),
        ('parcels', 'province_id', 'provinces', 'province_id'),
        ('neighborhoods', 'province_id', 'provinces', 'province_id'),
        ('subdivisions', 'province_id', 'provinces', 'province_id'),
    ]

    try:
        engine = sqlalchemy.create_engine(str(settings.database_url))
        with engine.connect() as connection:
            print("Successfully connected to the database.")
            
            with connection.begin():
                for table, fk_col, parent_table, parent_pk in fk_relationships:
                    print(f"Checking {table}.{fk_col} -> {parent_table}.{parent_pk}...")
                    
                    # Query to find orphaned rows
                    query_str = f"""
                        SELECT COUNT(*)
                        FROM {table} t
                        LEFT JOIN {parent_table} p ON CAST(t.{fk_col} AS BIGINT) = p.{parent_pk}
                        WHERE p.{parent_pk} IS NULL AND t.{fk_col} IS NOT NULL;
                    """
                    query = sqlalchemy.text(query_str)
                    orphaned_count = connection.execute(query).scalar_one()
                    
                    if orphaned_count > 0:
                        print(f"  -> Found {orphaned_count} orphaned row(s) in '{table}'.")
                        
                        delete_str = f"""
                            DELETE FROM {table}
                            WHERE CAST({fk_col} AS BIGINT) IN (
                                SELECT CAST(t_inner.{fk_col} AS BIGINT)
                                FROM {table} t_inner
                                LEFT JOIN {parent_table} p_inner ON CAST(t_inner.{fk_col} AS BIGINT) = p_inner.{parent_pk}
                                WHERE p_inner.{parent_pk} IS NULL AND t_inner.{fk_col} IS NOT NULL
                            );
                        """
                        if table == 'building_rules':
                            print("     -> Deleting orphaned rows from 'building_rules'.")
                            delete_query = sqlalchemy.text(delete_str)
                            connection.execute(delete_query)
                            print(f"  -> Successfully deleted {orphaned_count} orphaned rows from '{table}'.")
                        else:
                            # Update orphaned rows
                            update_str = f"""
                                UPDATE {table}
                                SET {fk_col} = NULL
                                WHERE CAST({fk_col} AS BIGINT) IN (
                                    SELECT CAST(t_inner.{fk_col} AS BIGINT)
                                    FROM {table} t_inner
                                    LEFT JOIN {parent_table} p_inner ON CAST(t_inner.{fk_col} AS BIGINT) = p_inner.{parent_pk}
                                    WHERE p_inner.{parent_pk} IS NULL AND t_inner.{fk_col} IS NOT NULL
                                );
                            """
                            update_query = sqlalchemy.text(update_str)
                            connection.execute(update_query)
                            print(f"  -> Successfully nulled {orphaned_count} orphaned foreign keys in '{table}'.")
                    else:
                        print(f"  -> No orphaned rows found in '{table}'.")

    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("Script finished successfully.")

if __name__ == "__main__":
    main() 
