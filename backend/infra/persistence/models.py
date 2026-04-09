from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from datetime import datetime, timezone
from .db import Base


class IntentMetric(Base):
    """Aggregate metrics only — no PII, no raw GPS, no user-generated content."""
    __tablename__ = "metrics_intents"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    emoji = Column(String)
    geohash_prefix = Column(String(4))  # ~20km precision — not PII
    created_at = Column(DateTime, default=datetime.now(timezone.utc))
    is_system = Column(Boolean, default=False)


class JoinMetric(Base):
    __tablename__ = "metrics_joins"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    joined_at = Column(DateTime, default=datetime.now(timezone.utc))


class MessageMetric(Base):
    __tablename__ = "metrics_messages"

    id = Column(Integer, primary_key=True, index=True)
    intent_id = Column(String, index=True)
    content_length = Column(Integer)
    sent_at = Column(DateTime, default=datetime.now(timezone.utc))
