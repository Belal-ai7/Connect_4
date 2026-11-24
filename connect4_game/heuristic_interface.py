"""
Heuristic INTERFACE for the Connect 4 minimax agent.

This file contains only the contract. The concrete heuristics live in
heuristic_implementations.py.

Contract (see Assignment 2, section 2.3)
----------------------------------------
Every heuristic is evaluated from the COMPUTER's point of view:
    * bigger  number -> computer is nearer to winning
    * smaller number -> human    is nearer to winning
"""

from abc import ABC, abstractmethod


class Heuristic(ABC):
    """Interface every heuristic must implement."""

    name = "base"            # short id used on the command line
    description = ""         # one line, shown in the game header / report

    @abstractmethod
    def evaluate(self, board) -> float:
        """Return the value of `board` for the computer (AI).

        `board` is a connect4.Board. Useful members:
            board.grid[row][col]  (row 0 = top)   values: EMPTY / HUMAN / AI
            board.heights[col]    discs in each column
            board.windows         list of every 4-cell line [(r, c) x 4]
            board.rows, board.cols
        The method must NOT modify the board.
        """

    def __call__(self, board):
        return self.evaluate(board)

    def __repr__(self):
        return f"<Heuristic {self.name}>"
