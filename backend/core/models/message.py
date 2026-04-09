from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, ConfigDict

class Message(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    intent_id: UUID
    user_id: UUID
    content: str = Field(min_length=1)
    created_at: datetime

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        import html
        v = html.escape(v.strip())
        if len(v) > 500:
            raise ValueError('Message content too long (max 500 chars)')
        if not v:
            raise ValueError('Message content cannot be empty')
        return v
