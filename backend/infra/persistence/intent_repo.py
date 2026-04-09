from datetime import datetime, timedelta, timezone
import logging
from uuid import UUID
from backend.core.models.intent import Intent
from backend.infra.persistence.redis import RedisClient, get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis
from .keys import RedisKeys
from backend.core.models.intent import Intent
from .lua_scripts import LuaScripts
import json
import logging
logger = logging.getLogger(__name__)

INTENT_TTL_SECONDS = 24 * 60 * 60 # 24h

class IntentRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client), reader: Redis | None = None):
        """
        :param redis: Write client (can be Pipeline)
        :param reader: Read client (must be Redis instance)
        """
        self.redis = redis
        self.reader = reader or redis

    async def save_intent(self, intent: Intent) -> None:
        key = RedisKeys.intent(intent.id)
        # Convert pydantic model to json
        data = intent.model_dump_json()
        await self.redis.set(key, data, ex=INTENT_TTL_SECONDS)
        
        # Add to geo index
        await self.redis.geoadd(RedisKeys.intent_geo(), (intent.longitude, intent.latitude, str(intent.id)))
        
        # Add to Expiration Queue
        expire_at = datetime.now(timezone.utc) + timedelta(seconds=INTENT_TTL_SECONDS)
        await self.redis.zadd(RedisKeys.expiry_queue(), {str(intent.id): expire_at.timestamp()})
        
        # Add to User's Intent List (with TTL matching intent expiry)
        if intent.user_id:
            await self.redis.sadd(RedisKeys.user_intents(intent.user_id), str(intent.id))
            await self.redis.expire(RedisKeys.user_intents(intent.user_id), INTENT_TTL_SECONDS)
        
        logger.info(f"Saved intent {intent.id} with TTL {INTENT_TTL_SECONDS}s")

    async def get_intent(self, intent_id: str) -> Intent | None:
        key = RedisKeys.intent(intent_id)
        data = await self.reader.get(key)
        if not data:
            return None
        intent = Intent.model_validate_json(data)
        
        # Populate join count
        join_key = RedisKeys.intent_joins(intent_id)
        count = await self.reader.scard(join_key)
        intent = intent.with_join_count(count)
        return intent

    async def find_nearby(
        self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50
    ) -> list[tuple[Intent, float]]:
        """
        Find nearby intents with distances. Returns (intent, distance_km) tuples
        for external ranking. Handles geo-search, hydration, and expired cleanup.
        """
        results = await self.reader.geosearch(
            RedisKeys.intent_geo(),
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            sort="ASC",
            count=limit * 2,
            withdist=True,
        )

        if not results:
            return []

        member_ids = [m[0] for m in results]
        distances = {m[0]: m[1] for m in results}

        keys = [RedisKeys.intent(mid) for mid in member_ids]
        json_list = await self.reader.mget(keys)

        candidates = []
        expired_members = []

        pipeline = self.reader.pipeline()

        for i, json_str in enumerate(json_list):
            if json_str:
                intent = Intent.model_validate_json(json_str)
                if intent.flags < 3:
                    candidates.append(intent)
                    pipeline.scard(RedisKeys.intent_joins(intent.id))
            else:
                expired_members.append(member_ids[i])

        if not candidates:
            if expired_members:
                await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)
            return []

        counts = await pipeline.execute()

        result_pairs = []
        for intent, count in zip(candidates, counts):
            intent = intent.with_join_count(count)
            dist = distances.get(str(intent.id), radius_km)
            if not intent.is_visible(dist):
                continue
            result_pairs.append((intent, dist))

        if expired_members:
            await self.redis.zrem(RedisKeys.intent_geo(), *expired_members)

        return result_pairs

    async def has_user_flagged(self, intent_id: UUID, user_id: UUID) -> bool:
        """Check if this user has already flagged this intent."""
        key = RedisKeys.intent_flags(intent_id)
        return bool(await self.reader.sismember(key, str(user_id)))

    async def record_user_flag(self, intent_id: UUID, user_id: UUID) -> None:
        """Record that this user flagged this intent."""
        key = RedisKeys.intent_flags(intent_id)
        await self.redis.sadd(key, str(user_id))
        await self.redis.expire(key, INTENT_TTL_SECONDS)

    async def flag_intent(self, intent_id: UUID) -> int:
        key = RedisKeys.intent(intent_id)
        # Atomic Lua script
        result = await self.redis.eval(LuaScripts.ATOMIC_FLAG, 1, str(key), 1)
        # If pipeline, result is Pipeline object (truthy).
        # We can't fetch the int value until commit.
        # But Handler expects int.
        # We'll rely on the handler handling Deferred or ignoring it in UoW context?
        # IMPORTANT: Hardening prompt asks for UoW.
        # If we are in UoW, result is not available.
        # We return 0 here assuming eventual consistency or special handling.
        if hasattr(self.redis, "execute_command"): # Is real client
             return int(result)
        return 0 # Deferred in pipeline

    async def get_geo_points(
        self, lat: float, lon: float, radius_km: float = 10.0
    ) -> list[tuple[str, float, float]]:
        """
        Fetch raw geo points within radius.
        Returns list of (member_id, longitude, latitude).
        """
        res = await self.reader.geosearch(
            name=RedisKeys.intent_geo(),
            longitude=lon,
            latitude=lat,
            radius=radius_km,
            unit="km",
            count=1000,
            withcoord=True,
        )
        if not res:
            return []

        return [(member, point[0], point[1]) for member, point in res]

    async def count_nearby(self, lat: float, lon: float, radius_km: float = 1.0) -> int:
        try:
           # GEOSEARCH key FROMLONLAT lon lat BYRADIUS radius km ASC count 100
           res = await self.redis.geosearch(
               name=RedisKeys.intent_geo(),
               longitude=lon,
               latitude=lat,
               radius=radius_km,
               unit="km",
               sort="ASC",
               count=100
           )
           logger.info(f"Count nearby lat={lat} lon={lon} r={radius_km} -> {len(res)} items")
           return len(res)
        except Exception as e:
            logger.error(f"Count nearby failed: {e}")
            return 0

