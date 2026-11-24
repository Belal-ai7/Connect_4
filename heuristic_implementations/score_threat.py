"""Assignment-focused heuristic using scores, threats, and candidate moves."""

from models import CellValue
from heuristic_interface import Heuristic

from .common import window_counts

AI = CellValue.FIRST
HUMAN = CellValue.SECOND
EMPTY = CellValue.EMPTY


class AssignmentHeuristic(Heuristic):
    """Estimate the final four-count advantage from the current position.

    The evaluation combines the current game score, playable moves that would
    complete one or more fours, open windows, and centre control. It is designed
    for the assignment's depth-limited minimax search; it is not an exact
    endgame solver.
    """

    name = "score_threat"
    description = "current score + candidate wins + playable threats"

    SCORE_WEIGHT = 500
    WINNING_POINT_WEIGHT = 200
    MULTI_FOUR_BONUS = 40
    THREAT_NOW_WEIGHT = 45
    THREAT_LATER_WEIGHT = 15
    TWO_DISC_WEIGHT = 8
    ONE_DISC_WEIGHT = 1
    CENTER_WEIGHT = 3

    def __init__(self):
        self._windows_by_shape = {}

    @staticmethod
    def _playable(board, row, col):
        """Return whether gravity allows a disc to land in this cell now."""
        return board.heights[col] == board.rows - 1 - row

    def _windows_by_cell(self, board):
        shape = (board.rows, board.cols)
        if shape not in self._windows_by_shape:
            by_cell = {(row, col): []
                       for row in range(board.rows)
                       for col in range(board.cols)}
            for window in board.windows:
                for cell in window:
                    by_cell[cell].append(window)
            self._windows_by_shape[shape] = by_cell
        return self._windows_by_shape[shape]

    def _four_lines_after_drop(self, board, col, player):
        """Count fours created by dropping ``player`` into ``col``."""
        row = board.rows - 1 - board.heights[col]
        board.grid[row][col] = player
        try:
            return sum(
                1
                for window in self._windows_by_cell(board)[(row, col)]
                if all(board.grid[r][c] == player for r, c in window)
            )
        finally:
            board.grid[row][col] = EMPTY

    def _candidate_points(self, board, player):
        """Return (winning columns, extra fours) for the given player."""
        points = extra_fours = 0
        for col, height in enumerate(board.heights):
            if height >= board.rows:
                continue
            fours = self._four_lines_after_drop(board, col, player)
            if fours:
                points += 1
                extra_fours += fours - 1
        return points, extra_fours

    def evaluate(self, board):
        ai_fours, human_fours = board.scores()
        score = (ai_fours - human_fours) * self.SCORE_WEIGHT

        ai_points, ai_extra_fours = self._candidate_points(board, AI)
        human_points, human_extra_fours = self._candidate_points(board, HUMAN)
        score += (ai_points - human_points) * self.WINNING_POINT_WEIGHT
        score += (ai_extra_fours - human_extra_fours) * self.MULTI_FOUR_BONUS

        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai and human:
                continue
            own = ai or human
            if own == 0 or own == 4:
                continue  # empty windows add nothing; completed fours are in score()

            sign = 1 if ai else -1
            if own == 3:
                row, col = next(
                    (r, c) for r, c in window if board.grid[r][c] == EMPTY
                )
                weight = (self.THREAT_NOW_WEIGHT if self._playable(board, row, col)
                          else self.THREAT_LATER_WEIGHT)
            elif own == 2:
                weight = self.TWO_DISC_WEIGHT
            else:
                weight = self.ONE_DISC_WEIGHT
            score += sign * weight

        middle = board.cols // 2
        for row in range(board.rows):
            value = board.grid[row][middle]
            if value == AI:
                score += self.CENTER_WEIGHT
            elif value == HUMAN:
                score -= self.CENTER_WEIGHT

        return score
