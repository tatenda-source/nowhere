import logging
from uuid import UUID
from backend.infra.persistence.redis import get_redis_client
from .keys import RedisKeys
from backend.core.models.message import Message
from fastapi import Depends
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class MessageRepository:
    def __init__(self, redis: Redis = Depends(get_redis_client), reader: Redis | None = None):
        """
        :param redis: Write client (can be Pipeline)
        :param reader: Read client (must be Redis instance)
        """
        self.redis = redis
        self.reader = reader or redis

    async def save_message(self, message: Message) -> None:
        intent_key = RedisKeys.intent(message.intent_id)
        messages_key = RedisKeys.intent_messages(message.intent_id)
        
        # Check intent existence/TTL using reader
        # This read happens outside the Write Transaction if pipeline is used.
        ttl = await self.reader.ttl(intent_key)
        if ttl <= 0:
            raise ValueError("Intent expired or not found")
        
        data = message.model_dump_json()
        
        # RPUSH to list (Write)
        await self.redis.rpush(messages_key, data)
        
        # Trim (Write)
        # Note: If count is Pipeline object (truthy), this always executes if condition is simplistic
        # But we need result of rpush to decide.
        # In pipeline, we can't decide.
        # So we should ALWAYS trim? Or use Lua?
        # For MVP Hardening, let's just blindly trim every time or use Lua.
        # Let's blindly trim. It's safe.
        await self.redis.ltrim(messages_key, -100, -1)
            
        # Refresh TTL (Write)
        await self.redis.expire(messages_key, ttl)
        
        logger.info(f"Saved message from {message.user_id} to intent {message.intent_id}")

    async def get_messages(self, intent_id: UUID, limit: int = 50) -> list[Message]:
        messages_key = RedisKeys.intent_messages(intent_id)
        # Get last N messages using reader
        raw_list = await self.reader.lrange(messages_key, -limit, -1)
        
        return [Message.model_validate_json(m) for m in raw_list]
