from typing import Protocol, List, Optional
from uuid import UUID
from ..models.intent import Intent
from ..models.message import Message

class IntentRepository(Protocol):
    async def save_intent(self, intent: Intent) -> None:
        ...

    async def get_intent(self, intent_id: str) -> Optional[Intent]:
        ...

    async def find_nearby(self, lat: float, lon: float, radius_km: float = 1.0, limit: int = 50) -> List[Intent]:
        ...
        
    async def get_clusters(self, lat: float, lon: float, radius_km: float = 10.0) -> List[dict]:
        ...

    async def flag_intent(self, intent_id: UUID) -> int:
        ...
        
    async def count_nearby(self, lat: float, lon: float, radius_km: float = 1.0) -> int:
        ...

class JoinRepository(Protocol):
    async def save_join(self, intent_id: UUID, user_id: UUID) -> bool:
        ...
        
    async def is_member(self, intent_id: UUID, user_id: UUID) -> bool:
        ...

class MessageRepository(Protocol):
    async def save_message(self, message: Message) -> None:
        ...
        
    async def get_messages(self, intent_id: UUID, limit: int = 50) -> List[Message]:
        ...

class MetricsRepository(Protocol):
    async def log_intent_creation(self, intent: Intent):
        ...
        
    async def log_join(self, intent_id: str, user_id: str):
        ...
        
    async def log_message(self, intent_id: str, user_id: str, content_length: int):
        ...
