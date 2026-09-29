from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Game, GamePlayer, Player


def get_or_create_player(db: Session, name: str) -> Player:
    player = db.scalar(select(Player).where(Player.name == name))
    if player is None:
        player = Player(name=name, points=0, games_played=0)
        db.add(player)
        db.commit()
        db.refresh(player)
    return player


def create_game_record(
    db: Session,
    join_code: str,
    difficulty: int,
    pot_points: int,
    player_names: list[str],
) -> Game:
    game = Game(
        join_code=join_code,
        difficulty=difficulty,
        status="playing",
        pot_points=pot_points,
    )
    db.add(game)
    db.flush()
    for name in player_names:
        player = get_or_create_player(db, name)
        db.add(
            GamePlayer(
                game_id=game.id,
                player_id=player.id,
                points_awarded=0,
                left_early=False,
            )
        )
    db.commit()
    db.refresh(game)
    return game


def _game_player(db: Session, game_id: int, name: str) -> tuple[Player, GamePlayer]:
    player = db.scalar(select(Player).where(Player.name == name))
    if player is None:
        raise RuntimeError(f"Unknown player {name}")
    link = db.scalar(
        select(GamePlayer).where(
            GamePlayer.game_id == game_id,
            GamePlayer.player_id == player.id,
        )
    )
    if link is None:
        raise RuntimeError(f"Player {name} is not in game {game_id}")
    return player, link


def mark_left_early(db: Session, game_id: int, name: str) -> None:
    player, link = _game_player(db, game_id, name)
    if link.left_early:
        return
    link.left_early = True
    link.points_awarded = 0
    player.games_played += 1
    db.commit()


def finish_game(
    db: Session,
    game_id: int,
    status: str,
    remaining_names: list[str],
    points_each: int,
) -> None:
    game = db.get(
        Game,
        game_id,
        options=[selectinload(Game.players).selectinload(GamePlayer.player)],
    )
    if game is None:
        raise RuntimeError(f"Unknown game {game_id}")
    game.status = status
    game.ended_at = datetime.now(timezone.utc).replace(tzinfo=None)
    remaining = set(remaining_names)
    for link in game.players:
        player = link.player
        if player.name in remaining and not link.left_early:
            link.points_awarded = points_each
            player.points += points_each
            player.games_played += 1
    db.commit()
