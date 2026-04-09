import logging
from uuid import UUID
from backend.infra.persistence.redis import get_redis_client
from .keys import RedisKeys
from fastapi import Depends
from redis.asyncio import Redis
from .lua_scripts import LuaScripts

logger = logging.getLogger(__name__)

class JoinRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client), reader: Redis | None = None):
        """
        :param redis: Write client (can be Pipeline)
        :param reader: Read client (must be Redis instance)
        """
        self.redis = redis
        self.reader = reader or redis

    async def save_join(self, intent_id: UUID, user_id: UUID) -> bool:
        """
        Adds user to intent joins using atomic Lua script.
        Checks if intent exists before joining.
        """
        intent_key = RedisKeys.intent(intent_id)
        join_key = RedisKeys.intent_joins(intent_id)
        
        # Atomic Lua: Check Intent Exists -> SADD -> EXPIRE
        result = await self.redis.eval(LuaScripts.SAVE_JOIN, 2, str(intent_key), str(join_key), str(user_id))
        
        # Handling pipeline result (Promise) vs Direct result
        if hasattr(self.redis, "execute_command"):
            if result == -1:
                raise ValueError("Intent not found or expired")
            
            added = (result == 1)
            if added:
                logger.info(f"User {user_id} joined intent {intent_id}")
            return added
            
        # Pipeline: We can't know result yet. Return True optimistically?
        # Or return False to be safe? 
        # Handler ignores result in UoW context usually.
        return True 

    async def get_join_count(self, intent_id: UUID) -> int:
        join_key = RedisKeys.intent_joins(intent_id)
        return await self.reader.scard(join_key)

    async def is_member(self, intent_id: UUID, user_id: UUID) -> bool:
        join_key = RedisKeys.intent_joins(intent_id)
        return await self.reader.sismember(join_key, str(user_id))
