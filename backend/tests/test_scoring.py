from app.game.scoring import pot_for_difficulty, split_points


def test_pot_scales_with_difficulty():
    assert pot_for_difficulty(1) == 20
    assert pot_for_difficulty(5) == 100


def test_points_are_split_evenly_with_integer_division():
    assert split_points(100, 4) == 25
    assert split_points(20, 3) == 6
    assert split_points(40, 0) == 0
