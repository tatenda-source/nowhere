from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime


class DomainEvent(BaseModel):
    """Base class for all domain events. Events represent facts that happened."""
    event_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    
    model_config = ConfigDict(frozen=True)


class IntentCreated(DomainEvent):
    """Event emitted when a new intent is created.
    GPS coordinates intentionally omitted — use coarse geohash for analytics only.
    """
    intent_id: UUID
    user_id: str
    emoji: str


class IntentJoined(DomainEvent):
    """Event emitted when a user joins an intent."""
    intent_id: UUID
    user_id: UUID


class MessagePosted(DomainEvent):
    """Event emitted when a message is posted to an intent."""
    message_id: UUID
    intent_id: UUID
    user_id: UUID
    content_length: int


class IntentFlagged(DomainEvent):
    """Event emitted when an intent is flagged."""
    intent_id: UUID
    new_flag_count: int
