from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, ConfigDict
from ..exceptions import InvalidAction

class Intent(BaseModel):
    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    user_id: str | None = None
    title: str = Field(min_length=1, max_length=50)
    emoji: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    created_at: datetime
    is_system: bool = False
    join_count: int = 0
    flags: int = 0

    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def round_coordinates(cls, v: float) -> float:
        return round(v, 3)

    @field_validator('emoji')
    @classmethod
    def validate_emoji(cls, v: str) -> str:
        if len(v) == 0 or len(v) > 4:
            raise ValueError('Emoji must be a single emoji character')
        return v
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()

    def flag(self) -> "Intent":
        """
        Transitions state to flagged. Returns a new instance.
        """
        return self.model_copy(update={"flags": self.flags + 1})

    def with_join_count(self, count: int) -> "Intent":
        """
        Returns a new instance with updated join count.
        """
        if count < 0:
            raise InvalidAction("Join count cannot be negative")
        return self.model_copy(update={"join_count": count})

    def is_visible(self, distance_km: float) -> bool:
        """
        Determines if the intent is visible at a given distance.
        Unverified intents (0 joins) are only visible within 200m.
        """
        if self.join_count == 0 and not self.is_system and distance_km > 0.2:
            return False
        return True

