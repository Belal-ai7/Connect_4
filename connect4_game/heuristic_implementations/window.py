"""Window-count heuristic with centre-column control."""

from ..models import CellValue
from ..heuristic_interface import Heuristic
from .common import window_counts

AI = CellValue.FIRST
HUMAN = CellValue.SECOND
EMPTY = CellValue.EMPTY


class WindowHeuristic(Heuristic):
    """Score open windows, playable threats, and centre-column discs."""

    name = "window"
    description = "threat-aware fours + open windows + centre control (default)"

    W = (0, 1, 10, 50, 1000)
    W_THREAT_NOW = 120
    W_THREAT_LATER = 40
    W_CENTER = 3

    @staticmethod
    def _playable(board, row, col):
        """Whether the empty cell is where the next disc would land."""
        return board.heights[col] == board.rows - 1 - row

    def evaluate(self, board):
        ai_score = human_score = 0
        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai and human:
                continue
            if ai:
                score = self._window_score(board, window, ai)
                ai_score += score
            elif human:
                score = self._window_score(board, window, human)
                human_score += score

        middle = board.cols // 2
        centre_cols = [middle] if board.cols % 2 else [middle - 1, middle]
        for row in range(board.rows):
            for col in centre_cols:
                if board.grid[row][col] == AI:
                    ai_score += self.W_CENTER
                elif board.grid[row][col] == HUMAN:
                    human_score += self.W_CENTER
        return ai_score - human_score

    def _window_score(self, board, window, disc_count):
        if disc_count == 3:
            row, col = next(
                (row, col)
                for row, col in window
                if board.grid[row][col] == EMPTY
            )
            return (self.W_THREAT_NOW if self._playable(board, row, col)
                    else self.W_THREAT_LATER)
        return self.W[disc_count]
