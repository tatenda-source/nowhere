import logging
from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from ..infra.persistence.redis import get_redis_client
from ..infra.persistence.event_store import STREAM_KEY

logger = logging.getLogger(__name__)

router = APIRouter()

# Simple Redis counters for operational metrics
COUNTER_PREFIX = "nowhere:counter:"


async def incr_counter(redis: Redis, name: str) -> None:
    """Increment an operational counter."""
    try:
        await redis.incr(f"{COUNTER_PREFIX}{name}")
    except Exception:
        pass


@router.get("/metrics")
async def get_metrics(redis: Redis = Depends(get_redis_client)):
    """Lightweight operational metrics endpoint."""
    pipe = redis.pipeline()
    counters = [
        "intents_created",
        "intents_joined",
        "messages_posted",
        "intents_flagged",
    ]
    for name in counters:
        pipe.get(f"{COUNTER_PREFIX}{name}")

    # Also get event stream length and geo index size
    pipe.xlen(STREAM_KEY)
    pipe.zcard("intents:geo")

    results = await pipe.execute()

    metrics = {}
    for name, val in zip(counters, results[: len(counters)]):
        metrics[name] = int(val) if val else 0

    metrics["event_stream_length"] = results[len(counters)]
    metrics["active_intents_geo"] = results[len(counters) + 1]

    return metrics
