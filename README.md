# Geospatial MVT Tile Processing Pipeline

This project is a high-performance, scalable pipeline for downloading, processing, and storing geospatial data from a Mapbox Vector Tile (MVT) server into a PostGIS database. It is designed to handle large geographical areas and massive datasets by intelligently offloading computationally intensive operations to the database.

## Key Features

- **Scalable Architecture**: Utilizes PostGIS for heavy-lifting geospatial operations (e.g., `ST_Union` for dissolving geometries), allowing it to process millions of features without being limited by local machine memory.
- **High-Performance Downloading**: Employs an asynchronous downloader (`aiohttp`) to fetch multiple MVT tiles concurrently.
- **Parallel Processing**: Decodes vector tiles in parallel using a `ProcessPoolExecutor` to maximize CPU usage.
- **Memory Efficient**: Processes data in batches, one layer at a time, to maintain a low memory footprint even with large datasets.
- **Configurable**: Pipeline parameters, such as the target bounding box, zoom level, and database connections, are managed through a simple `pipeline_config.yaml` file.
- **Robust & Maintainable**: The codebase is structured as a proper Python package (`src/suhail_pipeline`) with a clear entry point (`run_pipeline.py`) for execution.

## Architecture Overview

The pipeline operates in several distinct stages, orchestrated by the `PipelineOrchestrator`:

1.  **Tile Discovery**: Given a bounding box, it calculates all the XYZ tile coordinates required to cover the area at the specified zoom level.
2.  **Downloading**: Asynchronously downloads all required `.pbf` (MVT) tiles into a local cache (`tiles_cache/`).
3.  **Decoding**: Reads tiles from the cache and decodes them from the Protobuf format into GeoDataFrames. This CPU-bound step is parallelized across multiple processor cores.
4.  **Stitching & Persistence**:
    - For each geospatial layer (e.g., 'parcels', 'buildings'), all decoded geometries are streamed to a temporary table in PostGIS.
    - The `GeometryStitcher` executes a powerful SQL query (`ST_Union` grouped by a unique identifier) to dissolve and stitch the geometries directly on the database server.
    - The final, stitched geometries are saved to a permanent table in the database.
5.  **Cleanup**: Temporary tables in the database are dropped after the process completes.

This architecture was specifically chosen to overcome the performance and memory limitations of in-memory libraries like GeoPandas when dissolving millions of complex polygons.

## Prerequisites

- Python 3.8+
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)
- A running PostGIS instance. You can easily start one using the provided `docker-compose.yml`:
  ```bash
  docker-compose up -d
  ```

## Setup & Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd <repo-name>
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies using `uv`:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Configure the pipeline:**
    Open `pipeline_config.yaml` and edit the following sections:
    - `bounding_box`: Define the geographic area of interest (`min_lon`, `min_lat`, `max_lon`, `max_lat`).
    - `zoom_level`: Set the MVT zoom level to download.
    - `database`: Update the connection details for your PostGIS instance (host, port, user, password, dbname).

## How to Run the Pipeline

Once configured, execute the main run script:

```bash
python run_pipeline.py
```

The script will display progress bars for downloading, decoding, and processing each layer.

## Verifying the Output

A utility script, `check_db.py`, is provided to connect to the database and inspect the results.

- **List all tables in the public schema:**
  ```bash
  python check_db.py list-tables
  ```

- **Get the feature count for a specific table:**
  ```bash
  python check_db.py count <table_name>
  ```
  *Example:*
  ```bash
  python check_db.py count parcels
  ```

## Project Structure

```
.
├── .gitignore          # Ignores cache, temp files, and credentials
├── check_db.py         # Utility to verify database results
├── pipeline_config.yaml # Main configuration for the pipeline
├── README.md           # This file
├── requirements.txt    # Python dependencies
├── run_pipeline.py     # Main execution script
└── src/
    └── suhail_pipeline/ # The core pipeline as a Python package
        ├── __init__.py
        ├── config.py       # Loads and parses the YAML config
        ├── decoder/        # MVT decoding logic
        ├── downloader/     # Asynchronous tile downloader
        ├── geometry/       # Stitching and validation logic
        ├── persistence/    # PostGIS interaction module
        └── pipeline_orchestrator.py # Main orchestrator class
``` 