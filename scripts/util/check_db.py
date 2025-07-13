"""A simple script to connect to the database and list all tables."""

import typer
import sys
from pathlib import Path
from typing import Optional
from sqlalchemy import create_engine, inspect, text, exc
from meshic_pipeline.config import settings
from rich.table import Table as RichTable
from rich.console import Console
from sqlalchemy.exc import NoSuchTableError
import pandas as pd
from geoalchemy2.types import Geometry

app = typer.Typer()
console = Console()

# --- DB Connection Helper ---
def get_engine():
    try:
        engine = create_engine(str(settings.database_url))
        with engine.connect():
            pass
        return engine
    except exc.OperationalError as e:
        console.print(f"[bold red]--- DATABASE CONNECTION ERROR ---[/bold red]")
        console.print(f"Could not connect to the database using URL: {settings.database_url.path}")
        console.print("Please ensure the database server is running and the DATABASE_URL in your .env file is correct.")
        console.print(f"Details: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")
        raise typer.Exit(code=1)

# --- 1. List Schemas ---
@app.command()
def list_schemas():
    """List all schemas in the database."""
    engine = get_engine()
    inspector = inspect(engine)
    schemas = inspector.get_schema_names()
    console.print("[bold cyan]Schemas:[/bold cyan]")
    for s in schemas:
        console.print(f"- {s}")

# --- 2. List Tables ---
@app.command()
def list_tables(schema: str = typer.Option("public", help="Schema name (default: public)")):
    """List all tables in a schema."""
    engine = get_engine()
    inspector = inspect(engine)
    tables = inspector.get_table_names(schema=schema)
    console.print(f"[bold cyan]Tables in schema '{schema}':[/bold cyan]")
    for t in tables:
        console.print(f"- {t}")

# --- 3. List Columns (existing) ---
@app.command("list-columns")
def list_columns(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """Lists the columns and their types for a specific table."""
    engine = get_engine()
    inspector = inspect(engine)
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    try:
        columns = inspector.get_columns(table, schema=schema)
        rich_table = RichTable("Column", "Type")
        for column in columns:
            rich_table.add_row(column['name'], str(column['type']))
        console.print(rich_table)
    except Exception as e:
        console.print(f"[bold red]Could not retrieve columns for table '{table_name}'. Reason: {e}[/bold red]")
        raise typer.Exit(code=1)

# --- 4. Row Count ---
@app.command()
def row_count(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """Show row count for a table."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    with engine.connect() as conn:
        try:
            result = conn.execute(text(f'SELECT COUNT(*) FROM "{schema}"."{table}"'))
            count = result.scalar()
            console.print(f"[bold cyan]Row count for {table_name}: {count}[/bold cyan]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# --- 5. Sample Rows ---
@app.command()
def sample_rows(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels')."), limit: int = typer.Option(5, help="Number of rows to show.")):
    """Show sample rows from a table."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    with engine.connect() as conn:
        try:
            df = pd.read_sql(f'SELECT * FROM "{schema}"."{table}" LIMIT {limit}', conn)
            console.print(df)
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# --- 6. Indexes ---
@app.command()
def indexes(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """List indexes for a table."""
    engine = get_engine()
    inspector = inspect(engine)
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    try:
        idxs = inspector.get_indexes(table, schema=schema)
        rich_table = RichTable("Index Name", "Columns", "Unique")
        for idx in idxs:
            rich_table.add_row(idx['name'], ', '.join(idx['column_names']), str(idx['unique']))
        console.print(rich_table)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

# --- 7. Constraints ---
@app.command()
def constraints(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """List primary key and unique constraints for a table."""
    engine = get_engine()
    inspector = inspect(engine)
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    try:
        pk = inspector.get_pk_constraint(table, schema=schema)
        uniques = inspector.get_unique_constraints(table, schema=schema)
        console.print(f"[bold cyan]Primary Key: {pk.get('constrained_columns')}[/bold cyan]")
        if uniques:
            console.print("[bold cyan]Unique Constraints:[/bold cyan]")
            for uq in uniques:
                console.print(f"- {uq.get('name')}: {uq.get('column_names')}")
        else:
            console.print("No unique constraints.")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

# --- 8. Foreign Keys ---
@app.command()
def foreign_keys(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """List foreign key relationships for a table."""
    engine = get_engine()
    inspector = inspect(engine)
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    try:
        fks = inspector.get_foreign_keys(table, schema=schema)
        if not fks:
            console.print("No foreign keys.")
            return
        rich_table = RichTable("Constraint Name", "Columns", "Referred Table", "Referred Columns")
        for fk in fks:
            rich_table.add_row(fk.get('name', ''), ', '.join(fk['constrained_columns']), f"{fk['referred_schema']}.{fk['referred_table']}", ', '.join(fk['referred_columns']))
        console.print(rich_table)
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")

# --- 9. Table Size (Postgres only) ---
@app.command()
def table_size(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """Show disk usage for a table (Postgres only)."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    with engine.connect() as conn:
        try:
            # Use schema.table::regclass for Postgres
            sql = f"SELECT pg_size_pretty(pg_total_relation_size('{schema}.{table}'::regclass)) AS size;"
            result = conn.execute(text(sql))
            size = result.scalar()
            if size:
                console.print(f"[bold cyan]Table size for {schema}.{table}: {size}[/bold cyan]")
            else:
                console.print(f"[yellow]Could not retrieve table size for {schema}.{table}.[/yellow]")
        except Exception as e:
            if 'does not exist' in str(e):
                console.print(f"[bold red]Table {schema}.{table} does not exist.[/bold red]")
            else:
                console.print(f"[bold red]Error: {e}[/bold red]")

# --- 10. Check Nulls ---
@app.command()
def check_nulls(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels')."), column: str = typer.Argument(..., help="Column to check for NULLs.")):
    """Show count of NULLs in a column."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    inspector = inspect(engine)
    try:
        columns = [col['name'] for col in inspector.get_columns(table, schema=schema)]
        if column not in columns:
            console.print(f"[bold red]Column '{column}' does not exist in table {schema}.{table}.[/bold red]")
            raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error inspecting columns: {e}[/bold red]")
        raise typer.Exit(code=1)
    with engine.connect() as conn:
        try:
            sql = f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{column}" IS NULL'
            result = conn.execute(text(sql))
            count = result.scalar()
            console.print(f"[bold cyan]NULL count for {table_name}.{column}: {count}[/bold cyan]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# --- 11. List Views ---
@app.command()
def list_views(schema: str = typer.Option("public", help="Schema name (default: public)")):
    """List all views and materialized views in a schema."""
    engine = get_engine()
    inspector = inspect(engine)
    views = inspector.get_view_names(schema=schema)
    console.print(f"[bold cyan]Views in schema '{schema}':[/bold cyan]")
    for v in views:
        console.print(f"- {v}")
    # Materialized views (Postgres only)
    with engine.connect() as conn:
        try:
            sql = f"SELECT matviewname FROM pg_matviews WHERE schemaname = :schema"
            result = conn.execute(text(sql), {"schema": schema})
            matviews = [row[0] for row in result]
            if matviews:
                console.print(f"[bold cyan]Materialized Views:[/bold cyan]")
                for mv in matviews:
                    console.print(f"- {mv}")
        except Exception:
            pass

# --- 12. Recent Modifications ---
@app.command()
def recent_mods(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels')."), limit: int = typer.Option(5, help="Number of rows to show.")):
    """Show most recently modified rows (by created_at/updated_at if present)."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    with engine.connect() as conn:
        try:
            # Try updated_at, then created_at
            for col in ["updated_at", "created_at"]:
                sql = f'SELECT * FROM "{schema}"."{table}" ORDER BY "{col}" DESC LIMIT {limit}'
                try:
                    df = pd.read_sql(sql, conn)
                    if not df.empty:
                        console.print(f"[bold cyan]Most recent rows by {col}:[/bold cyan]")
                        console.print(df)
                        return
                except Exception:
                    continue
            console.print("[yellow]No created_at or updated_at column found, or no data.[/yellow]")
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

# --- 13. Export Schema ---
@app.command()
def export_schema(table_name: str = typer.Argument(..., help="The full name of the table (e.g., 'public.parcels').")):
    """Output CREATE TABLE SQL for a table (Postgres only)."""
    engine = get_engine()
    schema, table = table_name.split('.') if '.' in table_name else ('public', table_name)
    with engine.connect() as conn:
        try:
            # Try pg_get_tabledef (if available)
            sql = f"SELECT pg_get_tabledef('{schema}.{table}'::regclass);"
            result = conn.execute(text(sql))
            ddl = result.scalar()
            if ddl:
                console.print(f"[bold cyan]CREATE TABLE for {schema}.{table}:[/bold cyan]")
                console.print(ddl)
            else:
                console.print("[yellow]Could not retrieve table definition using pg_get_tabledef.[/yellow]")
        except Exception as e:
            if 'does not exist' in str(e):
                console.print(f"[bold red]Table {schema}.{table} does not exist.[/bold red]")
            elif 'function pg_get_tabledef' in str(e):
                console.print("[yellow]pg_get_tabledef is not available on this server. Please use pg_dump or information_schema for schema export.[/yellow]")
            else:
                console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == "__main__":
    app() 
