"""Shared helpers used by the heuristic modules."""

from constants import AI, HUMAN


def window_counts(board, window):
    """Return the AI and human disc counts for one four-cell window."""
    ai = human = 0
    for row, col in window:
        value = board.grid[row][col]
        if value == AI:
            ai += 1
        elif value == HUMAN:
            human += 1
    return ai, human
