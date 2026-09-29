from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.game.chat import ChatError
from app.game.global_chat import global_chat
from app.game.rooms import RoomError

router = APIRouter()


@router.websocket("/ws/global")
async def global_socket(websocket: WebSocket, name: str = Query(...)):
    await websocket.accept()
    try:
        name = await global_chat.connect(name, websocket)
    except (ChatError, RoomError) as exc:
        await websocket.send_json({"type": "error", "message": exc.message})
        await websocket.close(code=1008)
        return

    try:
        while True:
            message = await websocket.receive_json()
            try:
                if message.get("type") != "chat":
                    await websocket.send_json(
                        {"type": "error", "message": "Unknown message type"}
                    )
                    continue
                await global_chat.send_chat(name, message.get("message"))
            except ChatError as exc:
                await websocket.send_json({"type": "error", "message": exc.message})
            except (KeyError, TypeError, ValueError):
                await websocket.send_json(
                    {"type": "error", "message": "Invalid message"}
                )
    except WebSocketDisconnect:
        await global_chat.disconnect(name, websocket)
