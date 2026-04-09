from uuid import UUID
from typing import List
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.interfaces.repositories import IntentRepository, JoinRepository, MessageRepository, MetricsRepository
from ..core.exceptions import DomainError
from ..spam import SpamDetector
from ..core.clock import Clock

class IntentService:
    def __init__(
        self,
        intent_repo: IntentRepository,
        join_repo: JoinRepository,
        message_repo: MessageRepository,
        metrics_repo: MetricsRepository,
        spam_detector: SpamDetector,
        clock: Clock
    ):
        self.intent_repo = intent_repo
        self.join_repo = join_repo
        self.message_repo = message_repo
        self.metrics_repo = metrics_repo
        self.spam_detector = spam_detector
        self.clock = clock

    async def create_intent(
        self,
        title: str,
        emoji: str,
        latitude: float,
        longitude: float,
        user_id: str
    ) -> Intent:
        # Spam Check
        await self.spam_detector.check(title, user_id)

        # Create Domain Object
        intent = Intent(
            title=title,
            emoji=emoji,
            latitude=latitude,
            longitude=longitude,
            user_id=user_id,
            created_at=self.clock.now()
        )

        # Persistence
        await self.intent_repo.save_intent(intent)
        
        # Metrics
        # Note: In a real event-driven system, we'd embrace eventual consistency. 
        # Here we just fire and forget or await. The API layer used BackgroundTasks.
        # Ideally services shouldn't know about FastAPI BackgroundTasks.
        # We can make this method async and await it, or fire an event.
        # For MVP, await is fine (or fire_and_forget utility).
        await self.metrics_repo.log_intent_creation(intent)
        
        return intent

    async def get_nearby_intents(self, lat: float, lon: float, radius: float, limit: int) -> List[Intent]:
        return await self.intent_repo.find_nearby(lat, lon, radius, limit)

    async def get_clusters(self, lat: float, lon: float, radius: float) -> dict:
        clusters = await self.intent_repo.get_clusters(lat, lon, radius)
        return {"clusters": clusters}

    async def join_intent(self, intent_id: UUID, user_id: UUID) -> dict:
        try:
            joined = await self.join_repo.save_join(intent_id, user_id)
        except ValueError as e:
            # Map storage error to domain error if needed, or let it bubble
            # logic in repo raised ValueError("Intent not found or expired")
            # We should catch and re-raise DomainError if strict
            raise e 
        
        if joined:
            await self.metrics_repo.log_join(str(intent_id), str(user_id))
            
        return {"joined": joined, "intent_id": intent_id}

    async def post_message(self, intent_id: UUID, user_id: UUID, content: str) -> Message:
        # Spam Check
        await self.spam_detector.check(content, str(user_id))

        # Check membership
        if not await self.join_repo.is_member(intent_id, user_id):
             # We should define a specific exception for this
             raise DomainError("Must join intent to message")

        message = Message(
            intent_id=intent_id,
            user_id=user_id,
            content=content,
            created_at=self.clock.now()
        )
        
        await self.message_repo.save_message(message)
        
        await self.metrics_repo.log_message(str(intent_id), str(user_id), len(content))
        
        return message

    async def flag_intent(self, intent_id: UUID) -> dict:
        new_flags = await self.intent_repo.flag_intent(intent_id)
        return {"id": intent_id, "flags": new_flags}
