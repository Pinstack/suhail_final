from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from .models import Base


def get_db_engine(database_url=None):
    """Creates and returns a SQLAlchemy engine for sync operations."""
    import os
    url = database_url or os.environ.get('DATABASE_URL')
    return create_engine(str(url))


def get_async_db_engine():
    """Creates and returns an optimized async SQLAlchemy engine."""
    # Convert postgresql:// to postgresql+asyncpg://
    async_url = str(settings.database_url).replace("postgresql://", "postgresql+asyncpg://")
    return create_async_engine(
        async_url,
        pool_size=settings.db_pool.min_size,
        max_overflow=settings.db_pool.max_size - settings.db_pool.min_size,
        pool_pre_ping=settings.db_pool.pool_pre_ping,
        pool_recycle=settings.db_pool.pool_recycle,
        echo=settings.db_pool.echo_pool,
        # Memory optimization settings
        pool_timeout=settings.db_pool.timeout,
        connect_args={
            "command_timeout": settings.db_pool.command_timeout,
            "server_settings": {
                "application_name": "suhail_enrichment",
                "jit": "off",  # Disable JIT for memory optimization
            },
        },
    )


async def setup_database_async(engine):
    """Creates the necessary tables if they don't exist using async engine."""
    # import logging; logging.info("Setting up database tables...")
    with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    # import logging; logging.info("Tables checked/created successfully.")


def setup_database(engine):
    """Creates the necessary tables if they don't exist using sync engine."""
    # import logging; logging.info("Setting up database tables...")
    Base.metadata.create_all(engine, checkfirst=True)
    # import logging; logging.info("Tables checked/created successfully.")


def load_provinces_from_db(database_url=None):
    """Load province metadata from the provinces table and return as a dict keyed by province name (lowercase)."""
    engine = get_db_engine(database_url)
    with engine.connect() as conn:
        result = conn.execute(
            """
            SELECT province_id, province_name, province_name_ar, centroid_lon, centroid_lat, tile_server_url,
                   bbox_sw_lon, bbox_sw_lat, bbox_ne_lon, bbox_ne_lat
            FROM provinces
            """
        )
        provinces = {}
        for row in result:
            provinces[row['province_name'].lower()] = {
                "display_name": row['province_name'],
                "display_name_ar": row['province_name_ar'],
                "centroid": {
                    "lon": row['centroid_lon'],
                    "lat": row['centroid_lat'],
                },
                "bbox_latlon": {
                    "southwest": {"lat": row['bbox_sw_lat'], "lon": row['bbox_sw_lon']},
                    "northeast": {"lat": row['bbox_ne_lat'], "lon": row['bbox_ne_lon']},
                },
                "tile_url_template": row['tile_server_url'],
                "province_id": row['province_id'],
            }
        return provinces 