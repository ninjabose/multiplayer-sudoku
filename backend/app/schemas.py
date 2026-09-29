from __future__ import annotations

from pydantic import BaseModel, Field


class NameBody(BaseModel):
    name: str = Field(min_length=1, max_length=32)


class CreateRoomBody(NameBody):
    difficulty: int = Field(ge=1, le=5)


class LeaderboardEntry(BaseModel):
    name: str
    points: int
    games_played: int
