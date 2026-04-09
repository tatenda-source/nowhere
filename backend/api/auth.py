import logging
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from uuid import UUID, uuid4
from redis.asyncio import Redis
from ..auth.jwt import create_access_token
from ..infra.persistence.redis import get_redis_client
from ..infra.persistence.keys import RedisKeys
from .deps import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter()

class HandshakeRequest(BaseModel):
    # Ideally client sends their generated UUID if they have one but no JWT yet
    anon_id: str | None = None 

class HandshakeResponse(BaseModel):
    access_token: str
    token_type: str
    anon_id: str

@router.post("/handshake", response_model=HandshakeResponse)
async def handshake(request: HandshakeRequest):
    """
    Exchange an anonymous ID (or get a new one) for a signed JWT.
    """
    user_id = request.anon_id
    if not user_id:
        user_id = str(uuid4())
    else:
        # Validate UUID format
        try:
            UUID(user_id)
        except ValueError:
             raise HTTPException(status_code=400, detail="Invalid UUID format")
    
    # Create JWT
    access_token = create_access_token(data={"sub": user_id})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "anon_id": user_id
    }


@router.delete("/me/data", status_code=200)
async def delete_my_data(
    user_id: UUID = Depends(get_current_user_id),
    redis: Redis = Depends(get_redis_client),
):
    """
    GDPR Article 17 — Right to Erasure.
    Deletes all data associated with the authenticated user from Redis.
    """
    uid = str(user_id)
    deleted_keys = 0

    # 1. Find all intents created by this user
    user_intents_key = RedisKeys.user_intents(uid)
    intent_ids = await redis.smembers(user_intents_key)

    for intent_id in intent_ids:
        # Delete intent data, messages, joins, flags
        keys_to_delete = [
            RedisKeys.intent(intent_id),
            RedisKeys.intent_messages(intent_id),
            RedisKeys.intent_joins(intent_id),
            RedisKeys.intent_flags(intent_id),
        ]
        result = await redis.delete(*keys_to_delete)
        deleted_keys += result

        # Remove from geo index
        await redis.zrem(RedisKeys.intent_geo(), intent_id)

    # 2. Delete user's intent list
    await redis.delete(user_intents_key)
    deleted_keys += 1

    # 3. Delete rate limit keys
    for action in ("create_intent", "join", "message", "flag"):
        await redis.delete(RedisKeys.rate_limit(uid, action))

    # 4. Delete spam tracking
    await redis.delete(RedisKeys.spam_last_hash(uid))

    logger.info("GDPR erasure completed for user %s: %d keys deleted", uid, deleted_keys)
    return {"status": "deleted", "keys_removed": deleted_keys}
