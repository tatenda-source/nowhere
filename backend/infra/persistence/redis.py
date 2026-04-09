from typing import Optional
from urllib.parse import urlparse
from redis.asyncio import Redis, from_url
from redis.asyncio.retry import Retry
from redis.backoff import ExponentialBackoff
from contextlib import asynccontextmanager
from backend.config import settings
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


def _safe_redis_url(url: str) -> str:
    """Strip password from Redis URL for safe logging."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.hostname}:{parsed.port}{parsed.path}"


class RedisClient:
    _client: Optional[Redis] = None

    @classmethod
    def get_client(cls) -> Redis:
        if cls._client is None:
            raise RuntimeError("Redis client not initialized")
        return cls._client

    @classmethod
    async def connect(cls, redis_url: str = "redis://localhost:6379"):
        logger.info("Connecting to Redis at %s", _safe_redis_url(redis_url))
        cls._client = from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_timeout=5.0,
            socket_connect_timeout=5.0,
            retry_on_timeout=True,
            retry=Retry(ExponentialBackoff(), retries=3),
            health_check_interval=30,
        )
        await cls._client.ping()
        logger.info("Connected to Redis")

    @classmethod
    async def disconnect(cls):
        if cls._client:
            logger.info("Disconnecting from Redis")
            await cls._client.close()
            cls._client = None


# Dependency
async def get_redis_client() -> Redis:
    return RedisClient.get_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = getattr(settings, "REDIS_DSN", "redis://localhost:6379")
    await RedisClient.connect(redis_url)
    yield
    await RedisClient.disconnect()
