import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..auth.jwt import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_CONNECTIONS_PER_ROOM = 100
MAX_TOTAL_CONNECTIONS = 10000


class ConnectionManager:
    """Manages WebSocket connections per intent with limits."""

    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = {}
        self._total: int = 0

    def join(self, intent_id: str, ws: WebSocket) -> bool:
        if self._total >= MAX_TOTAL_CONNECTIONS:
            return False
        if intent_id not in self._rooms:
            self._rooms[intent_id] = set()
        if len(self._rooms[intent_id]) >= MAX_CONNECTIONS_PER_ROOM:
            return False
        self._rooms[intent_id].add(ws)
        self._total += 1
        return True

    def leave(self, intent_id: str, ws: WebSocket):
        room = self._rooms.get(intent_id)
        if room and ws in room:
            room.discard(ws)
            self._total -= 1
            if not room:
                del self._rooms[intent_id]

    async def broadcast(self, intent_id: str, data: dict, exclude: WebSocket | None = None):
        room = self._rooms.get(intent_id, set())
        dead = []
        for ws in room:
            if ws is exclude:
                continue
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            room.discard(ws)
            self._total -= 1


manager = ConnectionManager()


@router.websocket("/ws/intents/{intent_id}/messages")
async def intent_messages_ws(websocket: WebSocket, intent_id: str):
    # Validate intent_id is a UUID (prevent log injection / path traversal)
    try:
        UUID(intent_id)
    except ValueError:
        await websocket.close(code=4000, reason="Invalid intent ID")
        return

    # Authenticate via query param token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return

    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()

    if not manager.join(intent_id, websocket):
        await websocket.send_json({"type": "error", "message": "Room is full"})
        await websocket.close(code=4003, reason="Connection limit reached")
        return

    logger.info("WS connected to intent %s", intent_id)

    try:
        while True:
            # 60s timeout — evict abandoned connections (client should ping every 30s)
            data = await asyncio.wait_for(websocket.receive_text(), timeout=60)
            if data == "ping":
                await websocket.send_text("pong")
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    finally:
        manager.leave(intent_id, websocket)
        logger.info("WS disconnected from intent %s", intent_id)


def get_ws_manager() -> ConnectionManager:
    return manager
