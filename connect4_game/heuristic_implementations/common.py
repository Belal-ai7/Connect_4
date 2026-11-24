"""Shared helpers used by the heuristic modules."""

from ..models import CellValue

AI = CellValue.FIRST
HUMAN = CellValue.SECOND


def window_counts(board, window):
    ai = human = 0
    for row, col in window:
        value = board.grid[row][col]
        if value == AI:
            ai += 1
        elif value == HUMAN:
            human += 1
    return ai, human
