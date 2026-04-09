import asyncio
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
        logger.info("Subscribed handler to %s", event_type.__name__)

    async def publish(self, event: DomainEvent) -> None:
        """Persist event first, then dispatch to handlers in parallel.
        Handler failures are logged, not propagated."""
        if self._event_store:
            try:
                await self._event_store.append(event)
            except Exception as e:
                logger.error("Failed to persist event %s: %s", type(event).__name__, e, exc_info=True)

        event_type = type(event)
        handlers = self._handlers.get(event_type, [])

        if not handlers:
            return

        results = await asyncio.gather(
            *[handler(event) for handler in handlers],
            return_exceptions=True,
        )
        for r in results:
            if isinstance(r, Exception):
                logger.error("Event handler failed for %s: %s", event_type.__name__, r, exc_info=True)
