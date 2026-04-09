from typing import List, Any
from redis.asyncio import Redis
from backend.core.events import DomainEvent
from backend.core.event_bus import EventBus
from backend.infra.persistence.intent_repo import IntentRepository
from backend.infra.persistence.join_repo import JoinRepository
from backend.infra.persistence.message_repo import MessageRepository

class RedisUnitOfWork:
    def __init__(self, redis: Redis, event_bus: EventBus):
        self.redis = redis
        self.event_bus = event_bus
        self.pipeline = None
        self.events: List[DomainEvent] = []
        
        # Repositories (initialized in __aenter__)
        self.intent_repo: IntentRepository | None = None
        self.join_repo: JoinRepository | None = None
        self.message_repo: MessageRepository | None = None

    async def __aenter__(self) -> "RedisUnitOfWork":
        self.pipeline = self.redis.pipeline()
        # Initialize repositories with the pipeline as the write client
        # and the main redis instance as the read client.
        self.intent_repo = IntentRepository(redis=self.pipeline, reader=self.redis)
        self.join_repo = JoinRepository(redis=self.pipeline, reader=self.redis)
        self.message_repo = MessageRepository(redis=self.pipeline, reader=self.redis)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_type:
            await self.rollback()
            
    async def commit(self) -> None:
        if not self.pipeline:
            raise RuntimeError("Transaction not started")
            
        # Execute Redis transaction
        await self.pipeline.execute()
        
        # Publish events only if transaction succeeded
        for event in self.events:
            await self.event_bus.publish(event)
            
        # Clear events to avoid duplicate publishing if reused (though UoW is usually scoped)
        self.events.clear()

    async def rollback(self) -> None:
        if self.pipeline:
            # Redis pipeline has 'reset' but mostly we just discard the object in our logical flow.
            # There is no 'ROLLBACK' command in Redis if we haven't executed.
            # If we were strictly using MULTI/EXEC block, execute() does it.
            # If we want to discard, we just don't call execute().
            # So clearing pipeline object is enough.
            self.pipeline.reset()
        self.events.clear()

    def collect_event(self, event: DomainEvent) -> None:
        self.events.append(event)

    def get_events(self) -> List[DomainEvent]:
        return self.events
