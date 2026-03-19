import json
import logging
from typing import List
from redis.asyncio import Redis
from backend.core.events import DomainEvent

logger = logging.getLogger(__name__)

STREAM_KEY = "nowhere:events"
MAX_STREAM_LEN = 10000


class RedisEventStore:
    """Persists domain events to a Redis Stream for auditing and replay."""

    def __init__(self, redis: Redis):
        self.redis = redis

    async def append(self, event: DomainEvent) -> str:
        """Append an event to the stream. Returns the stream entry ID."""
        payload = {
            "event_type": type(event).__name__,
            "data": event.model_dump_json(),
        }
        entry_id = await self.redis.xadd(
            STREAM_KEY, payload, maxlen=MAX_STREAM_LEN, approximate=True
        )
        logger.debug(f"Event persisted: {type(event).__name__} -> {entry_id}")
        return entry_id

    async def read_since(self, last_id: str = "0-0", count: int = 100) -> List[dict]:
        """Read events from the stream after a given ID."""
        entries = await self.redis.xrange(STREAM_KEY, min=last_id, count=count)
        results = []
        for entry_id, fields in entries:
            results.append({
                "id": entry_id,
                "event_type": fields.get("event_type", ""),
                "data": json.loads(fields.get("data", "{}")),
            })
        return results

    async def stream_length(self) -> int:
        return await self.redis.xlen(STREAM_KEY)
