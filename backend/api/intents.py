from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from ..core.models.intent import Intent
from ..core.models.message import Message
from ..core.exceptions import IntentNotFound, DomainError, InvalidAction
from ..core.commands import CreateIntent, JoinIntent, PostMessage, FlagIntent
from ..core.clock import Clock
from .deps import get_current_user_id, get_intent_command_handler, get_intent_query_service, get_clock
from .limiter import RateLimiter, DynamicRateLimiter
from .message_schemas import CreateMessageRequest
from .join_schemas import JoinRequest
from .schemas import NearbyResponse, CreateIntentRequest, ClusterResponse
from ..services.intent_command_handler import IntentCommandHandler
from ..services.intent_query_service import IntentQueryService
from .ws import get_ws_manager

router = APIRouter()

@router.post("/", status_code=201, dependencies=[Depends(DynamicRateLimiter("create_intent", 5, 3600))])
async def create_intent(
    intent_request: CreateIntentRequest, 
    handler: IntentCommandHandler = Depends(get_intent_command_handler),
    user_id: str = Depends(get_current_user_id),
    clock: Clock = Depends(get_clock)
):
    cmd = CreateIntent(
        user_id=str(user_id),
        title=intent_request.title,
        emoji=intent_request.emoji,
        latitude=intent_request.latitude,
        longitude=intent_request.longitude,
        timestamp=clock.now()
    )
    
    try:
        return await handler.handle_create_intent(cmd)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.get("/nearby")
async def find_nearby_intents(
    lat: float,
    lon: float,
    radius: float = 1.0,
    limit: int = 50,
    query_service: IntentQueryService = Depends(get_intent_query_service),
):
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(status_code=422, detail="Invalid coordinates")
    if not (0.1 <= radius <= 50):
        raise HTTPException(status_code=422, detail="Radius must be between 0.1 and 50 km")
    limit = min(limit, 100)
    intents = await query_service.get_nearby(lat, lon, radius, limit)
    
    response = NearbyResponse(intents=intents, count=len(intents))
    if not intents:
        response.message = "It's quiet here. Start something?"
        
    return response

@router.get("/clusters")
async def get_intent_clusters(
    lat: float,
    lon: float,
    radius: float = 10.0,
    zoom: int | None = None,
    query_service: IntentQueryService = Depends(get_intent_query_service),
):
    return await query_service.get_clusters(lat, lon, radius, zoom)

@router.post("/{intent_id}/join", status_code=200, dependencies=[Depends(RateLimiter("join", 20, 3600))])
async def join_intent(
    intent_id: UUID, 
    user_id: UUID = Depends(get_current_user_id),
    handler: IntentCommandHandler = Depends(get_intent_command_handler),
    clock: Clock = Depends(get_clock)
):
    cmd = JoinIntent(
        intent_id=intent_id,
        user_id=user_id,
        timestamp=clock.now()
    )
    
    try:
        joined = await handler.handle_join_intent(cmd)
        if not joined:
            return {"joined": False, "intent_id": intent_id, "message": "Already joined"}
        return {"joined": True, "intent_id": intent_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DomainError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{intent_id}/messages", dependencies=[Depends(RateLimiter("message", 100, 3600))])
async def post_message(
    intent_id: UUID, 
    request: CreateMessageRequest, 
    user_id: UUID = Depends(get_current_user_id),
    handler: IntentCommandHandler = Depends(get_intent_command_handler),
    clock: Clock = Depends(get_clock)
):
    cmd = PostMessage(
        intent_id=intent_id,
        user_id=user_id,
        content=request.content,
        timestamp=clock.now()
    )
    
    try:
        message = await handler.handle_post_message(cmd)
        # Broadcast to WebSocket subscribers
        ws_manager = get_ws_manager()
        await ws_manager.broadcast(str(intent_id), {
            "type": "new_message",
            "message": {
                "id": str(message.id),
                "user_id": str(message.user_id),
                "content": message.content,
                "created_at": message.created_at.isoformat(),
            }
        })
        return message
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except DomainError as e:
        if "Must join" in str(e):
            raise HTTPException(status_code=403, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{intent_id}/flag", status_code=200, dependencies=[Depends(RateLimiter("flag", 5, 3600))])
async def flag_intent(
    intent_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    handler: IntentCommandHandler = Depends(get_intent_command_handler),
    clock: Clock = Depends(get_clock)
):
    cmd = FlagIntent(
        intent_id=intent_id,
        user_id=user_id,
        timestamp=clock.now()
    )
    return {"id": intent_id, "flags": await handler.handle_flag_intent(cmd)}
