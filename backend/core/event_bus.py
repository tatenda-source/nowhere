from typing import Protocol, List, Callable, Awaitable, Dict
from .events import DomainEvent
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Awaitable[None]]


class EventBus(Protocol):
    """Protocol for publishing and subscribing to domain events."""

    async def publish(self, event: DomainEvent) -> None:
        ...

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        ...


class InMemoryEventBus:
    """In-memory event bus with optional persistent event store."""

    def __init__(self, event_store=None):
        self._handlers: Dict[type, List[EventHandler]] = {}
        self._event_store = event_store

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Subscribed handler to {event_type.__name__}")

    async def publish(self, event: DomainEvent) -> None:
        """Persist event first, then dispatch to handlers. Handler failures are logged, not propagated."""
        # Persist to event store (if available)
        if self._event_store:
            try:
                await self._event_store.append(event)
            except Exception as e:
                logger.error(f"Failed to persist event {type(event).__name__}: {e}", exc_info=True)

        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            logger.debug(f"No handlers for {event_type.__name__}")
            return

        for handler in handlers:
            try:
                await handler(event)
                logger.debug(f"Handler executed for {event_type.__name__}")
            except Exception as e:
                logger.error(f"Event handler failed for {event_type.__name__}: {e}", exc_info=True)
