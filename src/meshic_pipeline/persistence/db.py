from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine
from meshic_pipeline.config import settings
from meshic_pipeline.logging_utils import get_logger
from .models import Base

logger = get_logger(__name__)


def get_db_engine():
    """Creates and returns a SQLAlchemy engine for sync operations."""
    return create_engine(str(settings.database_url))


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
    logger.info("Setting up database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    logger.info("Tables checked/created successfully.")


def setup_database(engine):
    """Creates the necessary tables if they don't exist using sync engine."""
    logger.info("Setting up database tables...")
    Base.metadata.create_all(engine, checkfirst=True)
    logger.info("Tables checked/created successfully.") 