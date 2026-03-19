import asyncio
import json
import logging
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..infra.persistence.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections per intent."""

    def __init__(self):
        self._rooms: dict[str, set[WebSocket]] = {}

    def join(self, intent_id: str, ws: WebSocket):
        if intent_id not in self._rooms:
            self._rooms[intent_id] = set()
        self._rooms[intent_id].add(ws)

    def leave(self, intent_id: str, ws: WebSocket):
        room = self._rooms.get(intent_id)
        if room:
            room.discard(ws)
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


manager = ConnectionManager()


@router.websocket("/ws/intents/{intent_id}/messages")
async def intent_messages_ws(websocket: WebSocket, intent_id: str):
    await websocket.accept()
    manager.join(intent_id, websocket)
    logger.info(f"WS connected to intent {intent_id}")

    try:
        while True:
            # Keep connection alive; client sends pings or messages
            data = await websocket.receive_text()
            # Client can send "ping" for keepalive
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        manager.leave(intent_id, websocket)
        logger.info(f"WS disconnected from intent {intent_id}")


def get_ws_manager() -> ConnectionManager:
    return manager
