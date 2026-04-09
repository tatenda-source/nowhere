from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class Join(BaseModel):
    intent_id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        frozen = True
