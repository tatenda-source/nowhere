from .db import AsyncSessionLocal
from .models import IntentMetric, JoinMetric, MessageMetric
from backend.core.models.intent import Intent
import logging

logger = logging.getLogger(__name__)


def _coarse_geohash(lat: float, lon: float) -> str:
    """Convert coordinates to a 4-char geohash (~20km precision) for aggregate analytics."""
    import hashlib
    # Simple grid-based bucketing — not a true geohash but sufficient for aggregate metrics
    lat_bucket = round(lat, 1)
    lon_bucket = round(lon, 1)
    return f"{lat_bucket},{lon_bucket}"


class MetricsRepository:
    async def log_intent_creation(self, intent: Intent):
        try:
            async with AsyncSessionLocal() as session:
                metric = IntentMetric(
                    intent_id=str(intent.id),
                    emoji=intent.emoji,
                    geohash_prefix=_coarse_geohash(intent.latitude, intent.longitude),
                    created_at=intent.created_at,
                    is_system=intent.is_system,
                )
                session.add(metric)
                await session.commit()
        except Exception as e:
            logger.error("Failed to log intent metric: %s", e)

    async def log_join(self, intent_id: str, user_id: str):
        try:
            async with AsyncSessionLocal() as session:
                metric = JoinMetric(intent_id=str(intent_id))
                session.add(metric)
                await session.commit()
        except Exception as e:
            logger.error("Failed to log join metric: %s", e)

    async def log_message(self, intent_id: str, user_id: str, content_length: int):
        try:
            async with AsyncSessionLocal() as session:
                metric = MessageMetric(
                    intent_id=str(intent_id),
                    content_length=content_length,
                )
                session.add(metric)
                await session.commit()
        except Exception as e:
            logger.error("Failed to log message metric: %s", e)
