from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Player
from app.schemas import LeaderboardEntry

router = APIRouter()


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(db: Session = Depends(get_db)):
    players = db.scalars(
        select(Player).order_by(Player.points.desc(), Player.games_played.desc(), Player.name)
    ).all()
    return [
        LeaderboardEntry(name=p.name, points=p.points, games_played=p.games_played)
        for p in players
    ]
