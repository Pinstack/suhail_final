"""A simple script to connect to the database and list all tables."""

import typer
from sqlalchemy import create_engine, inspect, text, exc
from src.suhail_pipeline.config import settings

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

if __name__ == "__main__":
    app() 