import redis.asyncio as redis
from backend.domain.models import Activity, Message, Join
from pydantic import BaseModel


def _serialize(obj: BaseModel) -> str:
    return obj.json()


def _key(prefix: str, id: str) -> str:
    return f"nowhere:{prefix}:{id}"


async def create_redis(dsn: str):
    r = redis.from_url(dsn, encoding="utf-8", decode_responses=True)
    # connection establishment (optional): ping to verify
    try:
        await r.ping()
    except Exception:
        pass
    return r


class RedisActivityRepo:
    def __init__(self, redis, ttl: int = 3600 * 6):
        self.redis = redis
        self.ttl = ttl

    async def save(self, activity: Activity):
        key = _key("activity", str(activity.id))
        await self.redis.set(key, _serialize(activity), ex=self.ttl)
        # GEO index maintenance if venue metadata provided
        if activity.metadata.get("location"):
            lat = activity.metadata["location"]["lat"]
            lon = activity.metadata["location"]["lon"]
            # store a geo point for discovery
            await self.redis.execute_command("GEOADD", "nowhere:activities:geo", lon, lat, str(activity.id))


class RedisJoinRepo:
    def __init__(self, redis, ttl: int = 3600 * 6):
        self.redis = redis
        self.ttl = ttl

    async def save(self, join: Join):
        key = _key("join", str(join.id))
        await self.redis.set(key, _serialize(join), ex=self.ttl)
        # maintain attendee set for activity
        await self.redis.sadd(_key("activity_attendees", str(join.activity_id)), str(join.attendee_id))
        await self.redis.expire(_key("activity_attendees", str(join.activity_id)), self.ttl)


class RedisMessageRepo:
    def __init__(self, redis, ttl: int = 3600 * 6):
        self.redis = redis
        self.ttl = ttl

    async def save(self, message: Message):
        key = _key("message", str(message.id))
        await self.redis.set(key, _serialize(message), ex=self.ttl)
        # push to activity message list
        await self.redis.rpush(_key("activity_messages", str(message.activity_id)), _serialize(message))
        await self.redis.expire(_key("activity_messages", str(message.activity_id)), self.ttl)
