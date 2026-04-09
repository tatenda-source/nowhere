from typing import Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class Activity(BaseModel):
    id: UUID
    type: str  # 'spontaneous' | 'venue'
    venue_id: Optional[UUID]
    organizer_id: Optional[UUID]
    title: str
    metadata: dict = {}
    created_at: datetime


class Attendee(BaseModel):
    id: UUID
    display_name: Optional[str]
    device_id: Optional[str]
    ephemeral: bool = True


class Join(BaseModel):
    id: UUID
    activity_id: UUID
    attendee_id: UUID
    joined_at: datetime


class Message(BaseModel):
    id: UUID
    activity_id: UUID
    attendee_id: UUID
    body: str
    sent_at: datetime


class Venue(BaseModel):
    id: UUID
    name: str
    location: dict  # {lat, lon}
    metadata: dict = {}


class OrganizerUser(BaseModel):
    id: UUID
    email: str
    name: Optional[str]
