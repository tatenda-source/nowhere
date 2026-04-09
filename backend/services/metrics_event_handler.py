from ..core.events import IntentCreated, IntentJoined, MessagePosted, IntentFlagged
from ..core.interfaces.repositories import MetricsRepository
import logging

logger = logging.getLogger(__name__)


class MetricsEventHandler:
    """Handles domain events by logging aggregate metrics (no PII)."""

    def __init__(self, metrics_repo: MetricsRepository):
        self.metrics_repo = metrics_repo

    async def on_intent_created(self, event: IntentCreated):
        """Log aggregate metrics when an intent is created."""
        from ..core.models.intent import Intent
        # Construct a minimal intent for the metrics API — no PII fields
        intent = Intent(
            id=event.intent_id,
            user_id=event.user_id,
            title="",  # Not stored in metrics
            emoji=event.emoji,
            latitude=0.0,  # Not stored in metrics — geohash derived at repo level
            longitude=0.0,
            created_at=event.timestamp,
        )
        await self.metrics_repo.log_intent_creation(intent)
        logger.debug("Logged metrics for intent creation: %s", event.intent_id)

    async def on_intent_joined(self, event: IntentJoined):
        await self.metrics_repo.log_join(str(event.intent_id), str(event.user_id))
        logger.debug("Logged metrics for intent join: %s", event.intent_id)

    async def on_message_posted(self, event: MessagePosted):
        await self.metrics_repo.log_message(
            str(event.intent_id),
            str(event.user_id),
            event.content_length,
        )
        logger.debug("Logged metrics for message: %s", event.message_id)

    async def on_intent_flagged(self, event: IntentFlagged):
        logger.info("Intent %s flagged, new count: %s", event.intent_id, event.new_flag_count)
