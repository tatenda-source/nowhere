import html
from pydantic import BaseModel, field_validator


class CreateMessageRequest(BaseModel):
    content: str

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        v = html.escape(v.strip())
        if not v:
            raise ValueError("Message content cannot be empty")
        if len(v) > 500:
            raise ValueError("Message content too long (max 500 characters)")
        return v
