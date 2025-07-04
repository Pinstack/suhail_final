import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from tabulate import tabulate


def get_db_connection():
    """Establishes a connection to the database using the DATABASE_URL from the .env file."""
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL not found in .env file or environment variables.")
    engine = create_engine(database_url)
    return engine.connect()


def get_schemas(connection):
    """Retrieves a list of all non-system schemas in the database."""
    query = text("""
        SELECT schema_name
        FROM information_schema.schemata
        WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'topology', 'tiger')
          AND schema_name NOT LIKE 'pg_temp_%'
          AND schema_name NOT LIKE 'pg_toast_temp_%';
    """)
    result = connection.execute(query)
    return [row[0] for row in result]


def get_tables_for_schema(connection, schema):
    """Retrieves a list of tables for a given schema."""
    query = text("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = :schema
        ORDER BY table_name;
    """)
    result = connection.execute(query, {'schema': schema})
    return [row[0] for row in result]


def get_table_details(connection, schema, table):
    """Retrieves column details for a given table, including data types and constraints."""
    query = text("""
        SELECT
            c.column_name,
            c.data_type,
            CASE WHEN c.is_nullable = 'YES' THEN 'NULL' ELSE 'NOT NULL' END as nullability,
            COALESCE(kcu.constraint_name, '') as pk,
            COALESCE(cc.check_clause, '') as "check"
        FROM information_schema.columns c
        LEFT JOIN information_schema.key_column_usage kcu
            ON c.table_schema = kcu.table_schema
            AND c.table_name = kcu.table_name
            AND c.column_name = kcu.column_name
            AND kcu.constraint_name IN (
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE constraint_type = 'PRIMARY KEY'
                AND table_schema = :schema
                AND table_name = :table
            )
        LEFT JOIN information_schema.check_constraints cc
            ON c.table_schema = cc.constraint_schema
            AND cc.constraint_name IN (
                SELECT constraint_name
                FROM information_schema.constraint_column_usage
                WHERE table_schema = :schema
                AND table_name = :table
                AND column_name = c.column_name
            )
        WHERE c.table_schema = :schema AND c.table_name = :table
        ORDER BY c.ordinal_position;
    """)
    result = connection.execute(query, {'schema': schema, 'table': table})
    return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_spatial_info(connection):
    """Retrieves information about spatial columns, including SRID and geometry type."""
    query = text("""
        SELECT
            f_table_schema,
            f_table_name,
            f_geometry_column,
            srid,
            type
        FROM
            geometry_columns;
    """)
    try:
        result = connection.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())
    except Exception:
        return pd.DataFrame() # Return empty dataframe if geometry_columns does not exist


def get_spatial_indexes(connection):
    """Retrieves information about spatial indexes (GiST)."""
    query = text("""
        SELECT
            n.nspname AS schemaname,
            c.relname AS tablename,
            i.relname AS indexname,
            a.attname AS columnname
        FROM
            pg_class c
        JOIN
            pg_index ix ON c.oid = ix.indrelid
        JOIN
            pg_class i ON i.oid = ix.indexrelid
        JOIN
            pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(ix.indkey)
        JOIN
            pg_namespace n ON n.oid = c.relnamespace
        JOIN
            pg_am am ON i.relam = am.oid
        WHERE
            c.relkind = 'r' AND i.relkind = 'i'
            AND am.amname IN ('gist', 'spgist')
            AND n.nspname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY
            schemaname, tablename, indexname;
    """)
    try:
        result = connection.execute(query)
        return pd.DataFrame(result.fetchall(), columns=result.keys())
    except Exception:
        return pd.DataFrame()


def get_foreign_keys(connection):
    """Retrieves all foreign key relationships in the database."""
    query = text("""
        SELECT
            tc.table_schema,
            tc.table_name,
            kcu.column_name,
            ccu.table_schema AS foreign_table_schema,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM
            information_schema.table_constraints AS tc
        JOIN
            information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
        JOIN
            information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
        WHERE
            tc.constraint_type = 'FOREIGN KEY';
    """)
    result = connection.execute(query)
    return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_json_columns_and_keys(connection, schema, table):
    """Identifies JSON/JSONB columns and extracts their top-level keys."""
    json_cols_query = text("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = :schema
          AND table_name = :table
          AND data_type IN ('json', 'jsonb');
    """)
    json_cols_result = connection.execute(json_cols_query, {'schema': schema, 'table': table})
    json_columns = [row[0] for row in json_cols_result]
    
    json_keys_summary = {}
    for col in json_columns:
        # Using a parameterized query for the column name is not straightforward,
        # so we ensure the column name is safe before embedding it.
        if not col.isalnum() and '_' not in col:
            continue

        keys_query = text(f"""
            SELECT jsonb_object_keys({col}::jsonb) AS key, COUNT(*) as count
            FROM {schema}.{table}
            WHERE {col} IS NOT NULL
            GROUP BY 1
            ORDER BY count DESC
            LIMIT 20;
        """)
        try:
            keys_result = connection.execute(keys_query)
            json_keys_summary[col] = [row[0] for row in keys_result]
        except Exception as e:
            # Handle cases where the column might not be jsonb or other errors
            print(f"Could not get keys for {schema}.{table}.{col}: {e}")
            json_keys_summary[col] = []
            
    return json_keys_summary

def main():
    """Main function to generate the database report."""
    report = []
    
    try:
        connection = get_db_connection()

        # 1. Database Structure Overview
        report.append("# 1. Database Structure Overview")
        schemas = get_schemas(connection)
        report.append(f"Found {len(schemas)} schemas: {', '.join(schemas)}")
        
        all_tables_details = {}
        for schema in schemas:
            report.append(f"\n## Schema: `{schema}`")
            tables = get_tables_for_schema(connection, schema)
            for table in tables:
                report.append(f"\n### Table: `{schema}.{table}`")
                details_df = get_table_details(connection, schema, table)
                report.append(tabulate(details_df, headers='keys', tablefmt='pipe'))
                all_tables_details[(schema, table)] = details_df

        # 2. Spatial Feature Summary
        report.append("\n# 2. Spatial Feature Summary")
        spatial_info = get_spatial_info(connection)
        if not spatial_info.empty:
            report.append("\n## Spatial Columns")
            report.append(tabulate(spatial_info, headers='keys', tablefmt='pipe'))
        else:
            report.append("\nNo spatial columns found in `geometry_columns`.")
            
        spatial_indexes = get_spatial_indexes(connection)
        if not spatial_indexes.empty:
            report.append("\n## Spatial Indexes")
            report.append(tabulate(spatial_indexes, headers='keys', tablefmt='pipe'))
        else:
            report.append("\nNo GiST/SP-GiST spatial indexes found.")

        foreign_keys = get_foreign_keys(connection)
        if not foreign_keys.empty:
            report.append("\n## Table Relationships (Foreign Keys)")
            report.append(tabulate(foreign_keys, headers='keys', tablefmt='pipe'))
        else:
            report.append("\nNo foreign key relationships found.")
            
        # Last part of user query: JSON analysis
        report.append("\n# JSON Column Analysis")
        for (schema, table), details in all_tables_details.items():
            if 'json' in details['data_type'].values or 'jsonb' in details['data_type'].values:
                report.append(f"\n## Analyzing JSON in `{schema}.{table}`")
                json_summary = get_json_columns_and_keys(connection, schema, table)
                for col, keys in json_summary.items():
                    report.append(f"\n### Column: `{col}`")
                    if keys:
                        report.append("Found common keys that could potentially be expanded:")
                        report.append("```\n" + "\n".join(f"- {key}" for key in keys) + "\n```")
                    else:
                        report.append("Could not determine common keys (column might be empty, not uniformly structured, or not jsonb).")

        # 3. Analytical & Visualization Potential
        report.append("\n# 3. Analytical & Visualization Potential")
        report.append("""
- **Proximity Analysis:** Calculate distances between spatial features (e.g., properties to parks, schools, transit stops).
- **Clustering:** Identify hotspots of real estate activity or areas with similar characteristics using algorithms like DBSCAN or K-means.
- **Overlay Analysis:** Combine layers to find intersections (e.g., properties within a specific zoning district or flood plain).
- **Network Analysis:** Analyze street networks to determine optimal routes, travel times, and accessibility.
- **Heatmaps:** Visualize the density of points, such as property sales, crime incidents, or business locations.
- **Choropleth Maps:** Map aggregated data by geographic area (e.g., average property price by neighborhood, population density by census tract).
- **Interactive Web Maps:** Create dynamic maps with tools like Leaflet, Mapbox, or Kepler.gl to allow users to explore the data, filter results, and view details on demand.
        """)

        # 4. Real Estate Use Cases
        report.append("\n# 4. Real Estate Use Cases")
        report.append("""
- **Site Selection:** Identify optimal locations for new developments (residential, commercial) based on demographics, accessibility, zoning, and market trends.
- **Market Analysis:** Understand pricing trends, absorption rates, and competitive landscapes by analyzing historical sales, listings, and neighborhood characteristics.
- **Risk Assessment:** Evaluate property exposure to environmental hazards (flooding, pollution), proximity to undesirable features (e.g., industrial zones), or infrastructure deficits.
- **Infrastructure Access:** Assess the value added by proximity to key amenities like public transit, major highways, schools, parks, and retail centers.
- **Beneficiaries:**
    - **Real Estate Brokers/Agents:** To advise clients on property values, market conditions, and investment opportunities.
    - **Developers:** To find and evaluate development sites and understand market demand.
    - **City Planners & Urbanists:** To analyze urban growth patterns, manage infrastructure, and develop zoning policies.
    - **Investors:** To identify undervalued assets and growth markets.
        """)

        # 5. Recommendations
        report.append("\n# 5. Recommendations")
        report.append("""
- **Standardize SRIDs:** Ensure all spatial layers use a consistent and appropriate Spatial Reference Identifier (SRID) for accurate spatial analysis. If multiple SRIDs are present, reproject data to a single standard (e.g., WGS 84 - SRID 4326 for global data, or a local projected system for regional analysis).
- **Improve Naming Conventions:** Adopt a clear and consistent naming convention for schemas, tables, and columns to improve readability and maintainability.
- **Add Missing Indexes:** Beyond spatial indexes, add B-tree indexes to foreign key columns and other frequently queried columns to improve join performance and query speed.
- **Create Materialized Views:** For complex queries or aggregations that are frequently accessed, create materialized views to pre-compute and store the results, leading to faster dashboards and analytics. Example: A view that joins property data with neighborhood names, average prices, and proximity scores to amenities.
- **Data Dictionary:** Create and maintain a data dictionary that describes each table, column, and its meaning, source, and update frequency.
        """)

    except Exception as e:
        report.append(f"An error occurred: {e}")
    finally:
        if 'connection' in locals() and not connection.closed:
            connection.close()

    with open("database_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    
    print("Database report generated successfully: database_report.md")


if __name__ == "__main__":
    main() 