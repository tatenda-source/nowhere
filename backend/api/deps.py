from fastapi import Request, HTTPException, Depends
from uuid import UUID
from redis.asyncio import Redis
from ..infra.persistence.redis import get_redis_client
from ..spam import SpamDetector
from ..infra.persistence.intent_repo import IntentRepository
from ..infra.persistence.join_repo import JoinRepository
from ..infra.persistence.message_repo import MessageRepository
from ..infra.persistence.metrics_repo import MetricsRepository
from ..services.intent_service import IntentService
from ..services.intent_command_handler import IntentCommandHandler
from ..services.intent_query_service import IntentQueryService
from ..services.metrics_event_handler import MetricsEventHandler
from ..core.clock import Clock, SystemClock
from ..core.event_bus import EventBus, InMemoryEventBus
from ..services.ranking_service import RankingService
from ..config import settings as app_settings
from ..core.events import IntentCreated, IntentJoined, MessagePosted, IntentFlagged
from ..infra.persistence.event_store import RedisEventStore
from ..core.unit_of_work import UnitOfWork
from ..infra.persistence.unit_of_work import RedisUnitOfWork


def get_current_user_id(request: Request) -> UUID:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    try:
        return UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid user ID")


# Global event bus instance (singleton pattern)
_event_bus = None


def get_clock() -> Clock:
    return SystemClock()


def get_intent_repo(redis: Redis = Depends(get_redis_client)) -> IntentRepository:
    return IntentRepository(redis=redis)


def get_join_repo(redis: Redis = Depends(get_redis_client)) -> JoinRepository:
    return JoinRepository(redis=redis)


def get_message_repo(redis: Redis = Depends(get_redis_client)) -> MessageRepository:
    return MessageRepository(redis=redis)


def get_metrics_repo(redis: Redis = Depends(get_redis_client)) -> MetricsRepository:
    return MetricsRepository(redis=redis)


def get_spam_detector(redis: Redis = Depends(get_redis_client)) -> SpamDetector:
    return SpamDetector(redis)


def get_event_bus(
    metrics_repo: MetricsRepository = Depends(get_metrics_repo),
    redis: Redis = Depends(get_redis_client),
) -> EventBus:
    """Get the global event bus instance and wire up handlers."""
    global _event_bus
    if _event_bus is None:
        event_store = RedisEventStore(redis)
        _event_bus = InMemoryEventBus(event_store=event_store)

        metrics_handler = MetricsEventHandler(metrics_repo)
        _event_bus.subscribe(IntentCreated, metrics_handler.on_intent_created)
        _event_bus.subscribe(IntentJoined, metrics_handler.on_intent_joined)
        _event_bus.subscribe(MessagePosted, metrics_handler.on_message_posted)
        _event_bus.subscribe(IntentFlagged, metrics_handler.on_intent_flagged)

    return _event_bus


def get_intent_service(
    intent_repo: IntentRepository = Depends(get_intent_repo),
    join_repo: JoinRepository = Depends(get_join_repo),
    message_repo: MessageRepository = Depends(get_message_repo),
    metrics_repo: MetricsRepository = Depends(get_metrics_repo),
    spam_detector: SpamDetector = Depends(get_spam_detector),
    clock: Clock = Depends(get_clock),
) -> IntentService:
    return IntentService(
        intent_repo=intent_repo,
        join_repo=join_repo,
        message_repo=message_repo,
        metrics_repo=metrics_repo,
        spam_detector=spam_detector,
        clock=clock,
    )


def get_unit_of_work(
    redis: Redis = Depends(get_redis_client),
    event_bus: EventBus = Depends(get_event_bus),
) -> UnitOfWork:
    return RedisUnitOfWork(redis=redis, event_bus=event_bus)


def get_intent_command_handler(
    uow: UnitOfWork = Depends(get_unit_of_work),
    spam_detector: SpamDetector = Depends(get_spam_detector),
) -> IntentCommandHandler:
    return IntentCommandHandler(uow=uow, spam_detector=spam_detector)


def get_ranking_service() -> RankingService:
    return RankingService(app_settings)


def get_intent_query_service(
    intent_repo: IntentRepository = Depends(get_intent_repo),
    ranking_service: RankingService = Depends(get_ranking_service),
) -> IntentQueryService:
    return IntentQueryService(intent_repo=intent_repo, ranking_service=ranking_service)
