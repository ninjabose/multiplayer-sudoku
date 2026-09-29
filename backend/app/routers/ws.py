from __future__ import annotations

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.db import session
from app.game.chat import ChatError
from app.game.rooms import RoomError, manager

router = APIRouter()


@router.websocket("/ws/rooms/{join_code}")
async def room_socket(websocket: WebSocket, join_code: str, name: str = Query(...)):
    await websocket.accept()
    name = name.strip()
    room = manager.get_by_code(join_code)
    if room is None or name not in room.players:
        await websocket.send_json({"type": "error", "message": "Cannot join this room"})
        await websocket.close(code=1008)
        return

    await manager.connect(room, name, websocket)
    try:
        while True:
            message = await websocket.receive_json()
            msg_type = message.get("type")
            db = session()
            try:
                if msg_type == "set_cell":
                    await manager.set_cell(
                        db,
                        room,
                        name,
                        int(message["row"]),
                        int(message["col"]),
                        int(message["value"]),
                    )
                elif msg_type == "give_up":
                    await manager.give_up(db, room, name)
                elif msg_type == "chat":
                    await manager.send_chat(room, name, message.get("message"))
                elif msg_type == "leave":
                    await manager.leave(db, room, name)
                    break
                else:
                    await websocket.send_json(
                        {"type": "error", "message": "Unknown message type"}
                    )
            except (RoomError, ChatError, KeyError, TypeError, ValueError) as exc:
                detail = (
                    exc.message
                    if isinstance(exc, (RoomError, ChatError))
                    else "Invalid message"
                )
                await websocket.send_json({"type": "error", "message": detail})
            finally:
                db.close()
    except WebSocketDisconnect:
        db = session()
        try:
            await manager.disconnect(db, room, name, websocket)
        finally:
            db.close()
