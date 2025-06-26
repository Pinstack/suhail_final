# Geospatial MVT Tile Processing Pipeline

This project is a high-performance, scalable pipeline for downloading, processing, and storing geospatial data from a Mapbox Vector Tile (MVT) server into a PostGIS database. It is designed to handle large geographical areas and massive datasets by intelligently offloading computationally intensive operations to the database.

It also includes a powerful data enrichment system to augment the geometric data with transaction history and building regulations from external APIs.

## Key Features

- **Scalable Architecture**: Utilizes PostGIS for heavy-lifting geospatial operations (e.g., `ST_Union` for dissolving geometries), allowing it to process millions of features without being limited by local machine memory.
- **Efficient Enrichment**: Intelligently enriches only the ~78,000 parcels with known transaction data, while providing an option for a full scan of all 1.1 million parcels if needed.
- **High-Performance Downloading**: Employs an asynchronous downloader (`aiohttp`) with a robust retry mechanism to fetch multiple MVT tiles and API data concurrently.
- **Parallel Processing**: Decodes vector tiles in parallel using a `ProcessPoolExecutor` to maximize CPU usage.
- **Configurable**: Pipeline parameters, such as the target bounding box, zoom level, and database connections, are managed through a simple `pipeline_config.yaml` file.
- **Rich CLI Utilities**: Provides a suite of command-line tools for database inspection, data verification, and running specific parts of the pipeline.

## Architecture Overview

The pipeline operates in two distinct but connected stages:

1.  **The Geometric Pipeline (`run_pipeline.py`)**: This is the core system responsible for discovering, downloading, and assembling the actual shapes (the polygons) of all land parcels from the MVT source. It populates the `public.parcels` table. This is an infrequent, heavy operation.
2.  **The Attribute Enrichment Pipeline (`enrich_parcels.py`)**: This is the system we've been working on. It takes the parcels from the first pipeline and enriches them with valuable data like transaction history and building rules from the Suhail API. This operation is designed to be run frequently and efficiently.

![Pipeline Diagram](https://i.imgur.com/your-diagram-image-url.png) <!-- You can replace this with a real image URL if you have one -->

## Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) (for package management)
- A running PostGIS instance.

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-name>
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies using `uv`:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Configure the pipeline:**
    Create a `.env` file for your database credentials and open `pipeline_config.yaml` to define the geographic area of interest (`bounding_box`) and `zoom_level`.

## Command-Line Utilities

This project includes two main command-line utilities: `enrich_parcels.py` for data enrichment and `check_db.py` for database inspection. Always ensure your virtual environment is active (`source .venv/bin/activate`) before running these commands.

### Data Enrichment (`enrich_parcels.py`)

This script fetches and stores additional data (transactions, building rules, price metrics) for parcels in the database.

**1. Run the efficient enrichment (Recommended for frequent use):**
This is the default command. It intelligently finds the ~78,000 parcels with a `transaction_price > 0` and enriches only them.

```bash
python enrich_parcels.py enrich
```

**2. Run a full-scan enrichment (Infrequent):**
Use the `--full-scan` flag to process all 1.1 million parcels in the database. This takes a very long time.

```bash
python enrich_parcels.py enrich --full-scan
```
*Optional Arguments:*
- `--batch-size <number>`: Set the number of parcels to process per API call (default: 100).
- `--limit <number>`: Limit the total number of parcels to process, for testing.

**3. Test data fetching for a single parcel:**
This command fetches all data for a specific parcel ID and prints it to the console without writing to the database. It is useful for debugging.

```bash
python enrich_parcels.py test-fetch --parcel-id <PARCEL_OBJECTID>
```
*Example:*
```bash
python enrich_parcels.py test-fetch --parcel-id 101000620207
```

---

### Database Inspection (`check_db.py`)

This script provides several tools for verifying the state of your PostGIS database.

**1. List all tables and their row counts:**
```bash
python check_db.py list-tables
```

**2. Summarize the parcels table:**
Provides a detailed breakdown of the `parcels` table, showing the total count and how many have transaction prices. This is the best way to verify the output of the Geometric Pipeline.

```bash
python check_db.py summarize-parcels
```

**3. List distinct values in a column:**
Counts the occurrences of each unique value in a specific column. Essential for understanding the diversity of your data.

```bash
python check_db.py list-distinct <schema.table> <column_name>
```
*Example (Standard Column):*
```bash
python check_db.py list-distinct public.parcels district_name
```
*Example (JSON Column):*
To query a key inside a JSON column (like `raw_data`), add the `--is-json` flag.
```bash
python check_db.py list-distinct public.transactions transactionSource --is-json
```

**4. List columns and their types for a table:**
```bash
python check_db.py list-columns <schema.table>
```
*Example:*
```bash
python check_db.py list-columns public.building_rules
```

**5. Get a feature count for a specific table:**
```bash
python check_db.py count <schema.table>
```
*Example:*
```bash
python check_db.py count public.transactions
```

**6. Get the total size of the database:**
```bash
python check_db.py get-db-size
```

## Core Geometric Pipeline (`run_pipeline.py`)

This is the main script that populates your `parcels` table from the MVT tile source.

**How to Run:**
Once `pipeline_config.yaml` is configured, execute the main run script:

```bash
python run_pipeline.py
```
The script will display progress bars for downloading, decoding, and processing each layer. 