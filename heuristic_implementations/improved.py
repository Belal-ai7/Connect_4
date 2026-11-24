"""Improved heuristic for Connect 4 minimax with alpha-beta pruning.

Positive values favour the AI, negative values favour the human.

Terms:
  1. score           - completed fours (AI minus human)
  2. immediate wins  - distinct playable columns where a drop completes a four
  3. double threats  - a side has two or more immediate winning columns
  4. multi-four      - one drop that completes several fours at once
  5. threats         - windows with 3 own discs and 1 empty cell:
                       playable ones weigh more; buried ones get a parity bonus
  6. partial windows - unblocked windows with 2 or 1 own discs
  7. centre          - column weight by distance from the middle column
"""

from models import CellValue
from heuristic_interface import Heuristic

from .common import window_counts

AI = CellValue.FIRST
HUMAN = CellValue.SECOND
EMPTY = CellValue.EMPTY


class ImprovedAssignmentHeuristic(Heuristic):
    """Heuristic for depth-limited minimax with alpha-beta pruning."""

    name = "improved"
    description = ("score + immediate wins + double threats + "
                   "parity-aware threats + centre")

    # Weights. Tune them by playing matches against the old heuristic.
    SCORE_WEIGHT = 1000
    IMMEDIATE_WIN_WEIGHT = 300
    DOUBLE_THREAT_WEIGHT = 500
    MULTI_FOUR_BONUS = 60
    THREAT_PLAYABLE_WEIGHT = 60
    THREAT_BURIED_WEIGHT = 20
    PARITY_BONUS = 25
    TWO_DISC_WEIGHT = 10
    ONE_DISC_WEIGHT = 1
    CENTER_WEIGHT = 4

    def __init__(self, ai_moves_first=True):
        """
        ai_moves_first: True if the AI is the first player to drop a disc.
        Used only for the parity bonus on buried threats.
        """
        self.ai_moves_first = ai_moves_first
        self._windows_by_shape = {}
        self.last_terms = {}  # per-term breakdown of the last evaluation

    # ----------------------------------------------------------------- helpers

    @staticmethod
    def _playable(board, row, col):
        """Return True if gravity allows a disc to land in this cell now."""
        return board.heights[col] == board.rows - 1 - row

    def _windows_by_cell(self, board):
        """Map each cell to the windows containing it (cached per board shape)."""
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
        """Count the fours that would be completed by dropping player into col."""
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

    def _immediate_wins(self, board, player):
        """Return (winning columns, extra fours beyond one per column)."""
        columns, extra = [], 0
        for col in range(board.cols):
            if board.heights[col] >= board.rows:
                continue  # column is full
            fours = self._four_lines_after_drop(board, col, player)
            if fours:
                columns.append(col)
                extra += fours - 1
        return columns, extra

    def _favoured_parity(self, owner):
        """Preferred row parity (counted from the bottom, 1-based) for owner.

        Returns 1 for odd rows, 0 for even rows. The first player benefits
        from odd-row threats and the second player from even-row threats.
        """
        owner_moves_first = (owner == AI) == self.ai_moves_first
        return 1 if owner_moves_first else 0

    def _threat_terms(self, board):
        """Return (AI threat total, human threat total) over all windows."""
        ai_total = human_total = 0
        for window in board.windows:
            ai, human = window_counts(board, window)
            if ai and human:
                continue  # blocked window, no value to either side
            own = ai or human
            if own in (0, 4):
                continue  # empty windows add nothing; fours are in the score

            owner = AI if ai else HUMAN
            if own == 3:
                row, col = next(
                    (r, c) for r, c in window if board.grid[r][c] == EMPTY
                )
                if self._playable(board, row, col):
                    weight = self.THREAT_PLAYABLE_WEIGHT
                else:
                    weight = self.THREAT_BURIED_WEIGHT
                    row_from_bottom = board.rows - row  # 1-based
                    if row_from_bottom % 2 == self._favoured_parity(owner):
                        weight += self.PARITY_BONUS
            elif own == 2:
                weight = self.TWO_DISC_WEIGHT
            else:
                weight = self.ONE_DISC_WEIGHT

            if owner == AI:
                ai_total += weight
            else:
                human_total += weight
        return ai_total, human_total

    def _centre_value(self, board):
        """Centre control: columns near the middle are worth more."""
        middle = (board.cols - 1) // 2
        total = 0
        for col in range(board.cols):
            column_weight = (board.cols + 1) // 2 - abs(col - middle)
            for row in range(board.rows):
                value = board.grid[row][col]
                if value == AI:
                    total += column_weight
                elif value == HUMAN:
                    total -= column_weight
        return total * self.CENTER_WEIGHT

    # --------------------------------------------------------------- evaluate

    def evaluate(self, board):
        """Return a number: large positive means the AI is closer to winning."""
        ai_fours, human_fours = board.scores()
        ai_cols, ai_extra = self._immediate_wins(board, AI)
        human_cols, human_extra = self._immediate_wins(board, HUMAN)
        ai_threat, human_threat = self._threat_terms(board)

        terms = {
            "score": (ai_fours - human_fours) * self.SCORE_WEIGHT,
            "immediate_wins": (len(ai_cols) - len(human_cols))
                              * self.IMMEDIATE_WIN_WEIGHT,
            "double_threats": (int(len(ai_cols) >= 2)
                               - int(len(human_cols) >= 2))
                              * self.DOUBLE_THREAT_WEIGHT,
            "multi_four": (ai_extra - human_extra) * self.MULTI_FOUR_BONUS,
            "threats": ai_threat - human_threat,
            "centre": self._centre_value(board),
        }
        self.last_terms = terms  # use this to print the value breakdown
        return sum(terms.values())
