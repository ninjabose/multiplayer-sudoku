from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.game.rooms import Room, RoomError, manager
from app.schemas import CreateRoomBody, NameBody

router = APIRouter()


def _http_error(exc: RoomError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


def serialize_room(room: Room) -> dict:
    data = room.public_state()
    data.pop("type", None)
    return data


@router.post("/rooms")
def create_room(body: CreateRoomBody, db: Session = Depends(get_db)):
    try:
        room = manager.create_room(db, body.name, body.difficulty)
    except RoomError as exc:
        raise _http_error(exc) from exc
    return serialize_room(room)


@router.post("/rooms/{join_code}/join")
async def join_room(join_code: str, body: NameBody, db: Session = Depends(get_db)):
    try:
        room = manager.join_room(db, join_code, body.name)
    except RoomError as exc:
        raise _http_error(exc) from exc
    await manager.broadcast(room)
    return serialize_room(room)


@router.post("/rooms/{join_code}/start")
async def start_room(join_code: str, body: NameBody, db: Session = Depends(get_db)):
    try:
        room = await manager.start_game(db, join_code, body.name)
    except RoomError as exc:
        raise _http_error(exc) from exc
    return serialize_room(room)


@router.get("/rooms/{join_code}")
def get_room(join_code: str):
    room = manager.get_by_code(join_code)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return serialize_room(room)
