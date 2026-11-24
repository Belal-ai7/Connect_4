"""Positional heuristic with playable and future threat scoring."""

from constants import AI, EMPTY, HUMAN
from heuristic_interface import Heuristic
from .common import window_counts


class PositionalHeuristic(Heuristic):
    """Score cell position, completed fours, and open two/three windows."""

    name = "positional"
    description = "fours + cell-value table + immediate vs. future threats"

    W_FOUR = 1000
    W_THREAT_NOW = 120
    W_THREAT_LATER = 40
    W_TWO = 8

    def __init__(self):
        self._tables = {}

    def _cell_table(self, board):
        key = (board.rows, board.cols)
        if key not in self._tables:
            table = [[0] * board.cols for _ in range(board.rows)]
            for window in board.windows:
                for row, col in window:
                    table[row][col] += 1
            self._tables[key] = table
        return self._tables[key]

    @staticmethod
    def _playable(board, row, col):
        """Whether a disc can be dropped in this cell on the next move."""
        return board.heights[col] == board.rows - 1 - row

    def evaluate(self, board):
        grid = board.grid
        table = self._cell_table(board)
        score = 0

        for row in range(board.rows):
            for col in range(board.cols):
                if grid[row][col] == AI:
                    score += table[row][col]
                elif grid[row][col] == HUMAN:
                    score -= table[row][col]

        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai and human:
                continue
            own = ai or human
            if not own:
                continue
            sign = 1 if ai else -1
            if own == 4:
                score += sign * self.W_FOUR
            elif own == 3:
                empty_row, empty_col = next(
                    (row, col) for row, col in window if grid[row][col] == EMPTY
                )
                weight = (self.W_THREAT_NOW if self._playable(board, empty_row, empty_col)
                          else self.W_THREAT_LATER)
                score += sign * weight
            elif own == 2:
                score += sign * self.W_TWO
        return score
