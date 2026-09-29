from __future__ import annotations

from app.game.sudoku import (
    CLUES_BY_LEVEL,
    clue_count,
    generate_puzzle,
    generate_solution,
    is_complete_and_valid,
)


def test_generated_solution_is_valid_sudoku():
    solution = generate_solution()
    assert is_complete_and_valid(solution)


def test_puzzle_matches_solution_on_clues_for_each_level():
    for difficulty, clues in CLUES_BY_LEVEL.items():
        puzzle, solution = generate_puzzle(difficulty)
        assert is_complete_and_valid(solution)
        assert clue_count(puzzle) == clues
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    assert puzzle[r][c] == solution[r][c]


def test_incomplete_board_is_not_valid():
    puzzle, _solution = generate_puzzle(1)
    assert not is_complete_and_valid(puzzle)
