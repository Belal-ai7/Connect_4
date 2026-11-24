"""Window-count heuristic with centre-column control."""

from constants import AI, HUMAN
from heuristic_interface import Heuristic
from .common import window_counts


class WindowHeuristic(Heuristic):
    """Score open four-cell windows and centre-column discs."""

    name = "window"
    description = "fours + open 3/2/1-windows + centre control (default)"

    W = (0, 1, 10, 50, 1000)
    W_CENTER = 3

    def evaluate(self, board):
        ai_score = human_score = 0
        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai and human:
                continue
            if ai:
                ai_score += self.W[ai]
            elif human:
                human_score += self.W[human]

        middle = board.cols // 2
        centre_cols = [middle] if board.cols % 2 else [middle - 1, middle]
        for row in range(board.rows):
            for col in centre_cols:
                if board.grid[row][col] == AI:
                    ai_score += self.W_CENTER
                elif board.grid[row][col] == HUMAN:
                    human_score += self.W_CENTER
        return ai_score - human_score
