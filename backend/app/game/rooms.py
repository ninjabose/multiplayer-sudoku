from __future__ import annotations

import asyncio
import secrets
import uuid
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket
from sqlalchemy.orm import Session

from app.game.chat import ChatError, RateLimiter, sanitize_chat_message, utc_timestamp
from app.game.persistence import (
    create_game_record,
    finish_game,
    get_or_create_player,
    mark_left_early,
)
from app.game.scoring import pot_for_difficulty, split_points
from app.game.sudoku import EMPTY, copy_board, generate_puzzle

MAX_PLAYERS = 4
JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
STATUSES_OPEN = {"lobby", "playing"}


def _new_join_code() -> str:
    return "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(6))


@dataclass
class Room:
    id: str
    join_code: str
    host: str
    difficulty: int
    status: str = "lobby"
    players: list[str] = field(default_factory=list)
    puzzle: list[list[int]] | None = None
    solution: list[list[int]] | None = None
    grid: list[list[int]] | None = None
    db_game_id: int | None = None
    connections: dict[str, WebSocket] = field(default_factory=dict)

    @property
    def pot_points(self) -> int:
        return pot_for_difficulty(self.difficulty)

    def public_state(self) -> dict[str, Any]:
        state: dict[str, Any] = {
            "type": "state",
            "room_id": self.id,
            "join_code": self.join_code,
            "host": self.host,
            "difficulty": self.difficulty,
            "status": self.status,
            "players": list(self.players),
            "connected": list(self.connections.keys()),
            "puzzle": self.puzzle,
            "grid": self.grid,
            "pot_points": self.pot_points,
        }
        if self.status == "given_up":
            state["solution"] = self.solution
        return state


class RoomError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class RoomManager:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}
        self._codes: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._chat_limiter = RateLimiter()

    def clear(self) -> None:
        self._rooms.clear()
        self._codes.clear()
        self._chat_limiter.clear()

    def get_by_code(self, join_code: str) -> Room | None:
        room_id = self._codes.get(join_code.upper())
        if room_id is None:
            return None
        return self._rooms.get(room_id)

    def _require_room(self, join_code: str) -> Room:
        room = self.get_by_code(join_code)
        if room is None:
            raise RoomError("Room not found", 404)
        return room

    def _make_code(self) -> str:
        for _ in range(20):
            code = _new_join_code()
            if code not in self._codes:
                return code
        raise RoomError("Could not allocate a join code", 500)

    def create_room(self, db: Session, name: str, difficulty: int) -> Room:
        name = _validate_name(name)
        if difficulty not in range(1, 6):
            raise RoomError("Difficulty must be between 1 and 5")
        get_or_create_player(db, name)
        room = Room(
            id=str(uuid.uuid4()),
            join_code=self._make_code(),
            host=name,
            difficulty=difficulty,
            players=[name],
        )
        self._rooms[room.id] = room
        self._codes[room.join_code] = room.id
        return room

    def join_room(self, db: Session, join_code: str, name: str) -> Room:
        name = _validate_name(name)
        room = self._require_room(join_code)
        if room.status != "lobby":
            raise RoomError("Game has already started")
        if name in room.players:
            raise RoomError("That name is already in this room")
        if len(room.players) >= MAX_PLAYERS:
            raise RoomError("Room is full")
        get_or_create_player(db, name)
        room.players.append(name)
        return room

    async def start_game(self, db: Session, join_code: str, name: str) -> Room:
        name = _validate_name(name)
        async with self._lock:
            room = self._require_room(join_code)
            if room.status != "lobby":
                raise RoomError("Game has already started")
            if name != room.host:
                raise RoomError("Only the host can start the game")
            puzzle, solution = generate_puzzle(room.difficulty)
            room.puzzle = puzzle
            room.solution = solution
            room.grid = copy_board(puzzle)
            room.status = "playing"
            game = create_game_record(
                db,
                join_code=room.join_code,
                difficulty=room.difficulty,
                pot_points=room.pot_points,
                player_names=list(room.players),
            )
            room.db_game_id = game.id
        await self.broadcast(room)
        return room

    async def connect(self, room: Room, name: str, ws: WebSocket) -> None:
        old = room.connections.get(name)
        room.connections[name] = ws
        if old is not None:
            try:
                await old.close()
            except Exception:
                pass
        await self.broadcast(room)

    async def set_cell(
        self, db: Session, room: Room, name: str, row: int, col: int, value: int
    ) -> None:
        async with self._lock:
            if room.status != "playing":
                raise RoomError("Game is not in progress")
            if name not in room.players:
                raise RoomError("You are not in this game")
            if room.puzzle is None or room.grid is None:
                raise RoomError("Board is not ready")
            if not (0 <= row < 9 and 0 <= col < 9):
                raise RoomError("Cell is out of range")
            if not (0 <= value <= 9):
                raise RoomError("Value must be 0-9")
            if room.puzzle[row][col] != EMPTY:
                raise RoomError("Cannot change a given clue")
            room.grid[row][col] = value
            if room.solution is not None and room.grid == room.solution:
                share = split_points(room.pot_points, len(room.players))
                if room.db_game_id is not None:
                    finish_game(db, room.db_game_id, "solved", list(room.players), share)
                room.status = "solved"
        await self.broadcast(room)

    async def send_chat(self, room: Room, name: str, raw_message: object) -> None:
        if room.status not in STATUSES_OPEN:
            raise ChatError("Chat is closed")
        if name not in room.players:
            raise ChatError("You are not in this room")
        text = sanitize_chat_message(raw_message)
        if not self._chat_limiter.allow(f"{room.id}:{name}"):
            raise ChatError("You are sending messages too quickly")
        payload = {
            "type": "chat",
            "username": name,
            "message": text,
            "timestamp": utc_timestamp(),
        }
        await self.broadcast_payload(room, payload)

    async def give_up(self, db: Session, room: Room, name: str) -> None:
        async with self._lock:
            if room.status != "playing":
                raise RoomError("Game is not in progress")
            if name not in room.players:
                raise RoomError("You are not in this game")
            if room.db_game_id is not None:
                finish_game(db, room.db_game_id, "given_up", list(room.players), 0)
            room.status = "given_up"
        await self.broadcast(room)

    async def leave(self, db: Session, room: Room, name: str) -> None:
        async with self._lock:
            await self._remove_player(db, room, name)
            should_broadcast = room.id in self._rooms
        if should_broadcast:
            await self.broadcast(room)

    async def disconnect(self, db: Session, room: Room, name: str, ws: WebSocket) -> None:
        async with self._lock:
            if room.connections.get(name) is not ws:
                return
            await self._remove_player(db, room, name)
            should_broadcast = room.id in self._rooms
        if should_broadcast:
            await self.broadcast(room)

    async def _remove_player(self, db: Session, room: Room, name: str) -> None:
        if name not in room.players:
            room.connections.pop(name, None)
            return
        ws = room.connections.pop(name, None)
        if ws is not None:
            try:
                await ws.close()
            except Exception:
                pass
        room.players.remove(name)
        self._chat_limiter.forget(f"{room.id}:{name}")
        if room.status == "playing" and room.db_game_id is not None:
            mark_left_early(db, room.db_game_id, name)
            if not room.players:
                finish_game(db, room.db_game_id, "abandoned", [], 0)
                room.status = "abandoned"
        elif room.status == "lobby":
            if not room.players:
                self._drop_room(room)
                return
            if room.host == name:
                room.host = room.players[0]
        if room.status not in STATUSES_OPEN and not room.connections:
            self._drop_room(room)

    def _drop_room(self, room: Room) -> None:
        self._rooms.pop(room.id, None)
        self._codes.pop(room.join_code, None)

    async def broadcast(self, room: Room) -> None:
        await self.broadcast_payload(room, room.public_state())

    async def broadcast_payload(self, room: Room, payload: dict[str, Any]) -> None:
        stale: list[str] = []
        for name, ws in list(room.connections.items()):
            try:
                await ws.send_json(payload)
            except Exception:
                stale.append(name)
        for name in stale:
            room.connections.pop(name, None)


def _validate_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise RoomError("Name is required")
    if len(cleaned) > 32:
        raise RoomError("Name must be 32 characters or fewer")
    return cleaned


manager = RoomManager()
