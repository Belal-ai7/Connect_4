"""Baseline heuristic that scores completed connect-fours only."""

from ..models import CellValue
from ..heuristic_interface import Heuristic
from .common import window_counts

AI = CellValue.FIRST
HUMAN = CellValue.SECOND


class ScoreHeuristic(Heuristic):
    """Difference of completed connect-fours; cheap but threat-blind."""

    name = "score"
    description = "completed fours difference only (baseline)"

    def evaluate(self, board):
        total = 0
        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai == 4:
                total += 1000
            elif human == 4:
                total -= 1000
        return total
