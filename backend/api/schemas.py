from typing import List, Optional
from pydantic import BaseModel
from ..core.models.intent import Intent

from pydantic import field_validator
import html


class CreateIntentRequest(BaseModel):
    title: str
    emoji: str
    latitude: float
    longitude: float

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        return html.escape(v.strip())[:100]

    @field_validator("emoji")
    @classmethod
    def sanitize_emoji(cls, v: str) -> str:
        return v.strip()[:4]

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        if not -90 <= v <= 90:
            raise ValueError("Latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        if not -180 <= v <= 180:
            raise ValueError("Longitude must be between -180 and 180")
        return v

class NearbyResponse(BaseModel):
    intents: List[Intent]
    count: int
    message: Optional[str] = None

class ClusterItem(BaseModel):
    geohash: str
    latitude: float
    longitude: float
    count: int

class ClusterResponse(BaseModel):
    clusters: List[ClusterItem]
