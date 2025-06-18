"""A simple script to connect to the database and list all tables."""

from src.suhail_pipeline.config import settings
from sqlalchemy import create_engine, inspect, exc, text

def main():
    """Connects to the database and lists all tables in all schemas."""
    print(f"Connecting to database: {settings.database_url.path}")
    try:
        engine = create_engine(str(settings.database_url))
        inspector = inspect(engine)
        schemas = inspector.get_schema_names()

        print("\\n--- Database Tables ---")
        for schema in schemas:
            # Don't inspect system schemas
            if schema.startswith('pg_') or schema == 'information_schema':
                continue
            
            print(f"Schema: {schema}")
            tables = inspector.get_table_names(schema=schema)
            if tables:
                for table in sorted(tables):
                    try:
                        with engine.connect() as connection:
                            result = connection.execute(text(f'SELECT COUNT(*) FROM {schema}."{table}"'))
                            count = result.scalar_one()
                            print(f"  - {table}: {count:,} features")
                    except Exception as e:
                        print(f"  - {table}: Could not count features. Reason: {e}")
            else:
                print("  - No tables found in this schema.")
        print("-----------------------")

    except exc.OperationalError as e:
        print("\\n--- ERROR ---")
        print("Could not connect to the database.")
        print(f"Please ensure PostgreSQL is running and the connection URL in your .env file is correct.")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main() 