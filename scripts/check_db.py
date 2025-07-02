"""A simple script to connect to the database and list all tables."""

import typer
import sys
import os
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy import create_engine, inspect, text, exc
from meshic_pipeline.config import settings
from rich.table import Table
from rich.console import Console
from sqlalchemy.exc import NoSuchTableError
from meshic_pipeline.decoder.mvt_decoder import MVTDecoder
import pandas as pd
from geoalchemy2.types import Geometry

app = typer.Typer()

def get_engine():
    """Creates and returns a SQLAlchemy engine."""
    try:
        engine = create_engine(str(settings.database_url))
        # Test the connection
        with engine.connect() as connection:
            pass
        return engine
    except exc.OperationalError as e:
        typer.echo(typer.style("--- DATABASE CONNECTION ERROR ---", fg=typer.colors.RED, bold=True))
        typer.echo(f"Could not connect to the database using URL: {settings.database_url.path}")
        typer.echo("Please ensure the database server is running and the DATABASE_URL in your .env file is correct.")
        typer.echo(f"Details: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(typer.style(f"An unexpected error occurred: {e}", fg=typer.colors.RED, bold=True))
        raise typer.Exit(code=1)

@app.command("list-tables")
def list_tables():
    """
    Connects to the database and lists all tables with their feature counts.
    """
    engine = get_engine()
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()

    typer.echo(typer.style("--- Database Tables ---", fg=typer.colors.CYAN, bold=True))
    for schema in sorted(schemas):
        if schema.startswith('pg_') or schema == 'information_schema':
            continue
        
        typer.echo(typer.style(f"Schema: {schema}", fg=typer.colors.YELLOW))
        tables = inspector.get_table_names(schema=schema)
        if tables:
            for table in sorted(tables):
                try:
                    with engine.connect() as connection:
                        result = connection.execute(text(f'SELECT COUNT(*) FROM {schema}."{table}"'))
                        count = result.scalar_one()
                        typer.echo(f"  - {table}: {count:,} features")
                except Exception as e:
                    typer.echo(f"  - {table}: Could not count features. Reason: {e}")
        else:
            typer.echo("  (No tables found)")
    typer.echo(typer.style("-----------------------", fg=typer.colors.CYAN, bold=True))

@app.command("count")
def count_features(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """
    Counts the number of features in a specific table.
    """
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    
    try:
        with engine.connect() as connection:
            result = connection.execute(text(f'SELECT COUNT(*) FROM {schema}."{table}"'))
            count = result.scalar_one()
            typer.echo(typer.style(f"Table '{table_name}' contains {count:,} features.", fg=typer.colors.GREEN))
    except Exception as e:
        typer.echo(typer.style(f"Error counting features in '{table_name}': {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

@app.command("get-db-size")
def get_db_size():
    """
    Calculates and prints the total size of the database.
    """
    engine = get_engine()
    db_name = engine.url.database
    
    if not db_name:
        typer.echo(typer.style("Could not determine database name from connection URL.", fg=typer.colors.RED))
        raise typer.Exit(code=1)
        
    try:
        with engine.connect() as connection:
            query = text("SELECT pg_size_pretty(pg_database_size(:db_name))")
            result = connection.execute(query, {"db_name": db_name})
            size = result.scalar_one()
            typer.echo(typer.style(f"Database '{db_name}' size: {size}", fg=typer.colors.GREEN, bold=True))
    except Exception as e:
        typer.echo(typer.style(f"Error calculating database size: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

@app.command("list-columns")
def list_columns(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """
    Lists the columns and their types for a specific table.
    """
    engine = get_engine()
    inspector = inspect(engine)
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)

    try:
        columns = inspector.get_columns(table, schema=schema)
        typer.echo(typer.style(f"--- Columns in {table_name} ---", fg=typer.colors.CYAN, bold=True))
        for column in columns:
            typer.echo(f"  - {column['name']}: {column['type']}")
        typer.echo(typer.style("----------------------------------", fg=typer.colors.CYAN, bold=True))

    except Exception as e:
        typer.echo(typer.style(f"Could not retrieve columns for table '{table_name}'. Reason: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

@app.command("list-distinct")
def list_distinct(
    table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.transactions')."),
    column_name: str = typer.Argument(..., help="The name of the column to find distinct values for."),
    is_json: bool = typer.Option(False, "--is-json", help="Set this flag if the column is a JSON field and you are querying a key within it.")
):
    """
    Lists the distinct values and their counts for a specific column in a table.
    For JSON columns, it queries for a specific key within the 'raw_data' field.
    """
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)

    if is_json:
        # Use JSON operator ->> to extract text field from the 'raw_data' column
        column_expression = f"raw_data->>'{column_name}'"
    else:
        # Standard query for a regular column
        column_expression = f'"{column_name}"'

    query = text(f"""
        SELECT 
            {column_expression} AS value, 
            COUNT(*) AS count
        FROM 
            {schema}."{table}" 
        GROUP BY 
            value
        ORDER BY 
            count DESC
    """)

    try:
        with engine.connect() as connection:
            result = connection.execute(query)
            rows = result.fetchall()
            if not rows:
                typer.echo(typer.style(f"No distinct values found in '{column_name}' for table '{table_name}'.", fg=typer.colors.YELLOW))
                return

            typer.echo(typer.style(f"--- Distinct values in {table_name}.{column_name} ---", fg=typer.colors.CYAN, bold=True))
            for row in rows:
                value, count = row
                # Handle None from JSON extraction
                value_str = "NULL" if value is None else value
                typer.echo(f"  - {value_str}: {count:,} records")
            typer.echo(typer.style("--------------------------------------------------", fg=typer.colors.CYAN, bold=True))

    except Exception as e:
        typer.echo(typer.style(f"Error fetching distinct values for '{table_name}.{column_name}': {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)

@app.command("summarize-parcels")
def summarize_parcels():
    """
    Provides a summary of the public.parcels table, including transaction data status.
    """
    engine = get_engine()
    typer.echo(typer.style("--- Parcel Summary ---", fg=typer.colors.CYAN, bold=True))

    try:
        with engine.connect() as connection:
            # Total parcels
            total_count_result = connection.execute(text('SELECT COUNT(*) FROM public.parcels'))
            total_count = total_count_result.scalar_one()
            typer.echo(f"Total Parcels: {total_count:,}")

            # Parcels with NULL transaction_price
            null_price_result = connection.execute(text('SELECT COUNT(*) FROM public.parcels WHERE transaction_price IS NULL'))
            null_price_count = null_price_result.scalar_one()
            typer.echo(f"Parcels with NULL transaction_price: {null_price_count:,}")

            # Parcels with 0 transaction_price
            zero_price_result = connection.execute(text('SELECT COUNT(*) FROM public.parcels WHERE transaction_price = 0'))
            zero_price_count = zero_price_result.scalar_one()
            typer.echo(f"Parcels with 0 transaction_price: {zero_price_count:,}")

            # Parcels with transaction_price > 0
            positive_price_count = total_count - null_price_count - zero_price_count
            typer.echo(f"Parcels with transaction_price > 0: {positive_price_count:,}")

    except Exception as e:
        typer.echo(typer.style(f"Error summarizing parcels table: {e}", fg=typer.colors.RED))
        raise typer.Exit(code=1)
    finally:
        typer.echo(typer.style("----------------------", fg=typer.colors.CYAN, bold=True))

@app.command(name="verify-tile-schema")
def verify_tile_schema_command(
    tile_path: str = typer.Argument(..., help="Path to the MVT tile file (e.g., tiles_cache/15/20636/14069.pbf).")
):
    """Compares an MVT tile's schema against the live PostGIS database."""
    from pathlib import Path
    
    tile_p = Path(tile_path)
    if not tile_p.exists():
        typer.echo(typer.style(f"❌ Error: Tile file not found at '{tile_path}'", fg=typer.colors.RED, bold=True))
        raise typer.Exit(code=1)

    typer.echo(typer.style(f"--- Verifying schema for tile: {tile_path} ---", fg=typer.colors.BLUE, bold=True))

    # 1. Decode Tile
    with open(tile_p, "rb") as f:
        tile_data = f.read()
    
    try:
        z, x, y = map(int, [tile_p.parent.parent.name, tile_p.parent.name, tile_p.stem])
    except (ValueError, AttributeError):
        typer.echo(typer.style("❌ Error: Could not determine tile Z/X/Y from path structure.", fg=typer.colors.RED, bold=True))
        raise typer.Exit(code=1)

    decoder = MVTDecoder()
    decoded_layers = decoder.decode_to_gdf(tile_data, z, x, y)

    # 2. Connect to DB
    engine = get_engine()
    inspector = inspect(engine)

    # 3. Compare Schemas
    for layer_name, gdf in decoded_layers.items():
        if layer_name == 'streets':
            continue

        table_name = settings.table_name_mapping.get(layer_name, layer_name)
        typer.echo(typer.style(f"\n🔎 Verifying Layer '{layer_name}' -> Table 'public.{table_name}'", fg=typer.colors.GREEN, bold=True))

        if gdf.empty:
            typer.echo(typer.style("  - GDF is empty, skipping schema check.", fg=typer.colors.YELLOW))
            continue

        try:
            db_columns = inspector.get_columns(table_name, schema="public")
            db_schema = {col['name']: col['type'] for col in db_columns}
        except NoSuchTableError:
            typer.echo(typer.style(f"  - ⚠️  Warning: Table 'public.{table_name}' not found.", fg=typer.colors.YELLOW))
            continue

        gdf_schema = {col: gdf[col].dtype for col in gdf.columns}

        # Compare
        table = Table(title="Column Type Comparison")
        table.add_column("Column Name", style="cyan")
        table.add_column("MVT-derived Type", style="magenta")
        table.add_column("DB Type", style="yellow")
        table.add_column("Status", style="bold")

        all_cols = sorted(set(gdf_schema.keys()) | set(db_schema.keys()))
        
        for col_name in all_cols:
            gdf_type_str = str(gdf_schema.get(col_name, 'N/A'))
            db_type_obj = db_schema.get(col_name)
            db_type_str = str(db_type_obj).split('(')[0] if db_type_obj is not None else 'N/A'
            
            status = ""
            if col_name not in gdf_schema:
                status = "✅ DB only"
            elif col_name not in db_schema:
                status = "❌ MVT only"
            else: # Both exist, compare types
                 if col_name == 'geometry':
                    if isinstance(db_type_obj, Geometry):
                        status = "✅ OK"
                    else:
                        status = "❌ MISMATCH"
                 elif pd.api.types.is_integer_dtype(gdf_schema[col_name]) and "INT" in db_type_str:
                    status = "✅ OK"
                 elif pd.api.types.is_float_dtype(gdf_schema[col_name]) and ("FLOAT" in db_type_str or "DOUBLE" in db_type_str):
                    status = "✅ OK"
                 elif pd.api.types.is_object_dtype(gdf_schema[col_name]) and "VARCHAR" in db_type_str or "TEXT" in db_type_str:
                    status = "✅ OK"
                 else:
                    status = "❌ MISMATCH"

            table.add_row(col_name, gdf_type_str, db_type_str, status)
        
        console = Console()
        console.print(table)

if __name__ == "__main__":
    app() 