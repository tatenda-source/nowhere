import asyncio
import logging

from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# Only initialize SQLAlchemy engine if Postgres is enabled.
# This avoids importing aiosqlite (removed from prod deps) when
# POSTGRES_ENABLED=false, which is the default on Render.
engine = None
AsyncSessionLocal = None

if settings.POSTGRES_ENABLED:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

    engine = create_async_engine(
        settings.POSTGRES_DSN,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_timeout=10,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )


async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("PostgreSQL is not enabled")
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    if engine is None:
        logger.info("PostgreSQL disabled — skipping DB init.")
        return
    logger.info("Initializing Database...")
    try:
        async with asyncio.timeout(3.0):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.warning("Failed to initialize DB: %s", e)
