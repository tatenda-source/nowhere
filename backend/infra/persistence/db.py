import asyncio
import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

logger = logging.getLogger(__name__)

# Engine with production-ready pool configuration
engine = create_async_engine(
    settings.POSTGRES_DSN,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

# Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    logger.info("Initializing Database...")
    try:
        async with asyncio.timeout(3.0):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized.")
    except Exception as e:
        logger.warning("Failed to initialize DB: %s", e)
