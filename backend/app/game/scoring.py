from __future__ import annotations

POINTS_BY_LEVEL = {
    1: 20,
    2: 40,
    3: 60,
    4: 80,
    5: 100,
}


def pot_for_difficulty(difficulty: int) -> int:
    if difficulty not in POINTS_BY_LEVEL:
        raise ValueError("Difficulty must be an integer from 1 to 5")
    return POINTS_BY_LEVEL[difficulty]


def split_points(pot: int, player_count: int) -> int:
    if player_count <= 0:
        return 0
    return pot // player_count
