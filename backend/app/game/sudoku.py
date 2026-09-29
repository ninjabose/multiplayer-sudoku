from __future__ import annotations

import random

SIZE = 9
BOX = 3
EMPTY = 0

# More clues = easier. Level 1 is easiest, level 5 is hardest.
CLUES_BY_LEVEL = {
    1: 46,
    2: 38,
    3: 30,
    4: 24,
    5: 18,
}

Board = list[list[int]]


def empty_board() -> Board:
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]


def copy_board(board: Board) -> Board:
    return [row[:] for row in board]


def _in_box(board: Board, row: int, col: int, value: int) -> bool:
    br = (row // BOX) * BOX
    bc = (col // BOX) * BOX
    for r in range(br, br + BOX):
        for c in range(bc, bc + BOX):
            if board[r][c] == value:
                return True
    return False


def can_place(board: Board, row: int, col: int, value: int) -> bool:
    if value in board[row]:
        return False
    if any(board[r][col] == value for r in range(SIZE)):
        return False
    if _in_box(board, row, col, value):
        return False
    return True


def _find_empty(board: Board) -> tuple[int, int] | None:
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == EMPTY:
                return r, c
    return None


def _fill(board: Board) -> bool:
    pos = _find_empty(board)
    if pos is None:
        return True
    row, col = pos
    nums = list(range(1, SIZE + 1))
    random.shuffle(nums)
    for value in nums:
        if can_place(board, row, col, value):
            board[row][col] = value
            if _fill(board):
                return True
            board[row][col] = EMPTY
    return False


def generate_solution() -> Board:
    board = empty_board()
    if not _fill(board):
        raise RuntimeError("Failed to generate a Sudoku solution")
    return board


def generate_puzzle(difficulty: int) -> tuple[Board, Board]:
    if difficulty not in CLUES_BY_LEVEL:
        raise ValueError("Difficulty must be an integer from 1 to 5")
    solution = generate_solution()
    puzzle = copy_board(solution)
    clues = CLUES_BY_LEVEL[difficulty]
    to_remove = SIZE * SIZE - clues
    cells = [(r, c) for r in range(SIZE) for c in range(SIZE)]
    random.shuffle(cells)
    for i in range(to_remove):
        r, c = cells[i]
        puzzle[r][c] = EMPTY
    return puzzle, solution


def is_complete_and_valid(board: Board) -> bool:
    if len(board) != SIZE or any(len(row) != SIZE for row in board):
        return False
    expected = set(range(1, SIZE + 1))
    for row in board:
        if set(row) != expected:
            return False
    for col in range(SIZE):
        if {board[r][col] for r in range(SIZE)} != expected:
            return False
    for br in range(0, SIZE, BOX):
        for bc in range(0, SIZE, BOX):
            box = [board[r][c] for r in range(br, br + BOX) for c in range(bc, bc + BOX)]
            if set(box) != expected:
                return False
    return True


def clue_count(puzzle: Board) -> int:
    return sum(cell != EMPTY for row in puzzle for cell in row)
