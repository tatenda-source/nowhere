from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID, uuid4
from datetime import datetime


class Command(BaseModel):
    """Base class for all commands. Commands represent write operations."""
    command_id: UUID = Field(default_factory=uuid4)
    timestamp: datetime
    
    model_config = ConfigDict(frozen=True)


class CreateIntent(Command):
    """Command to create a new intent."""
    user_id: str
    title: str
    emoji: str
    latitude: float
    longitude: float


class JoinIntent(Command):
    """Command to join an existing intent."""
    intent_id: UUID
    user_id: UUID


class PostMessage(Command):
    """Command to post a message to an intent."""
    intent_id: UUID
    user_id: UUID
    content: str


class FlagIntent(Command):
    """Command to flag an intent for moderation."""
    intent_id: UUID
    user_id: UUID
