from fastapi import HTTPException
from redis.asyncio import Redis
from hashlib import sha256
import re
import logging
from .infra.persistence.keys import RedisKeys

logger = logging.getLogger(__name__)

class SpamDetector:
    def __init__(self, redis: Redis):
        self.redis = redis

    async def check(self, content: str, user_id: str):
        """
        Runs heuristic checks and repetition checks.
        Raises HTTPException(400) if spam detected.
        """
        if not content:
            return

        # 1. Heuristics
        
        # A. Length limits (already enforced by Pydantic mostly, but logic check)
        if len(content) > 500:
             raise HTTPException(status_code=400, detail="Content too long")

        # B. Caps Lock (Allow if short < 5 chars)
        if len(content) > 5 and content.isupper():
            raise HTTPException(status_code=400, detail="Please turn off caps lock")

        # C. Repeated Characters (e.g. "loooooooool")
        # Match any character repeated more than 4 times
        if re.search(r'(.)\1{4,}', content):
            raise HTTPException(status_code=400, detail="Please ease up on the repeated keys")

        # 2. Repetition (Dedup)
        # Hash content
        content_hash = sha256(content.encode()).hexdigest()
        key = RedisKeys.spam_last_hash(user_id)
        
        last_hash = await self.redis.get(key)
        if last_hash and last_hash == content_hash:
            raise HTTPException(status_code=400, detail="You just posted that. Be original!")
        
        # Save new hash (expire in 5 mins - prevent spamming same thing)
        await self.redis.set(key, content_hash, ex=300)

