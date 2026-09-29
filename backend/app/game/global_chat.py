from __future__ import annotations

from fastapi import WebSocket

from app.game.chat import ChatError, RateLimiter, sanitize_chat_message, utc_timestamp
from app.game.rooms import RoomError, _validate_name

MAX_GLOBAL_USERS = 50


class GlobalChatManager:
    def __init__(self) -> None:
        self.connections: dict[str, WebSocket] = {}
        self._limiter = RateLimiter()

    def clear(self) -> None:
        self.connections.clear()
        self._limiter.clear()

    async def connect(self, name: str, ws: WebSocket) -> str:
        name = _validate_name(name)
        if name not in self.connections and len(self.connections) >= MAX_GLOBAL_USERS:
            raise ChatError("Global chat is full")
        old = self.connections.get(name)
        self.connections[name] = ws
        if old is not None:
            try:
                await old.close()
            except Exception:
                pass
        await self._broadcast_presence()
        return name

    async def disconnect(self, name: str, ws: WebSocket) -> None:
        if self.connections.get(name) is not ws:
            return
        self.connections.pop(name, None)
        self._limiter.forget(name)
        await self._broadcast_presence()

    async def send_chat(self, name: str, raw_message: object) -> None:
        if name not in self.connections:
            raise ChatError("You are not connected to global chat")
        text = sanitize_chat_message(raw_message)
        if not self._limiter.allow(name):
            raise ChatError("You are sending messages too quickly")
        payload = {
            "type": "chat",
            "username": name,
            "message": text,
            "timestamp": utc_timestamp(),
        }
        await self._broadcast(payload)

    async def _broadcast_presence(self) -> None:
        await self._broadcast(
            {
                "type": "presence",
                "users": sorted(self.connections.keys()),
            }
        )

    async def _broadcast(self, payload: dict) -> None:
        stale: list[str] = []
        for name, ws in list(self.connections.items()):
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(name)
        for name in stale:
            self.connections.pop(name, None)
            self._limiter.forget(name)


global_chat = GlobalChatManager()
