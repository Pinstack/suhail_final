from sqlalchemy.engine import Engine
from sqlalchemy import text


def reset_temp_table(engine: Engine, prod_table: str, temp_table: str):
    """
    Drops and recreates a temp table with the same schema as the production table.
    Uses Postgres 'CREATE TABLE ... LIKE ... INCLUDING ALL'.
    Args:
        engine (Engine): SQLAlchemy engine connected to the target database.
        prod_table (str): Name of the production table to copy schema from.
        temp_table (str): Name of the temp table to create/reset.
    """
    with engine.begin() as conn:
        conn.execute(text(f'DROP TABLE IF EXISTS "{temp_table}"'))
        conn.execute(text(f'CREATE TABLE "{temp_table}" (LIKE "{prod_table}" INCLUDING ALL)'))

# Optionally, add more utilities here as needed for temp table management. 