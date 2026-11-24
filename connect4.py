#!/usr/bin/env python3
"""
Connect 4 - Human vs. Computer
==============================
AI agent: Minimax with alpha-beta pruning, depth-limited to K levels and
evaluated with a custom heuristic at the cut-off.

Game rules (per Assignment 2):
  * The board is ROWS x COLS (default 6 x 7).
  * Players alternate dropping discs. The game continues until the board is FULL.
  * Score of a player = number of connected-fours (horizontal, vertical,
    diagonal; overlapping fours all count). Greater score wins.

Usage:
    python connect4.py --k 4
    python connect4.py --k 5 --first ai --tree-file trees.txt
    python connect4.py --k 3 --no-tree          # hide the tree on the console
"""

import argparse
import sys
import time

from constants import AI, EMPTY, HUMAN, SYMBOL, TERMINAL_MULT
from heuristic_interface import Heuristic
from heuristic_implementations import DEFAULT as DEFAULT_HEURISTIC
from heuristic_implementations import REGISTRY as HEURISTICS
from heuristic_implementations import get_heuristic

INF = float("inf")


# --------------------------------------------------------------------------- #
#  Board
# --------------------------------------------------------------------------- #
class Board:
    """Grid stored as grid[row][col], row 0 = TOP, row ROWS-1 = BOTTOM."""

    def __init__(self, rows=6, cols=7):
        self.rows = rows
        self.cols = cols
        self.grid = [[EMPTY] * cols for _ in range(rows)]
        self.heights = [0] * cols          # discs currently in each column
        self.moves_made = 0
        # Pre-compute every window of 4 cells once (huge speed-up).
        self.windows = self._build_windows()
        # Column order: centre first -> better alpha-beta pruning.
        centre = (cols - 1) / 2
        self.col_order = sorted(range(cols), key=lambda c: (abs(c - centre), c))

    # ---- helpers ---------------------------------------------------------- #
    def _build_windows(self):
        wins = []
        R, C = self.rows, self.cols
        for r in range(R):
            for c in range(C):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    er, ec = r + 3 * dr, c + 3 * dc
                    if 0 <= er < R and 0 <= ec < C:
                        wins.append([(r + i * dr, c + i * dc) for i in range(4)])
        return wins

    def copy(self):
        b = Board.__new__(Board)
        b.rows, b.cols = self.rows, self.cols
        b.grid = [row[:] for row in self.grid]
        b.heights = self.heights[:]
        b.moves_made = self.moves_made
        b.windows = self.windows
        b.col_order = self.col_order
        return b

    def valid_moves(self):
        return [c for c in self.col_order if self.heights[c] < self.rows]

    def is_full(self):
        return self.moves_made == self.rows * self.cols

    def drop(self, col, player):
        row = self.rows - 1 - self.heights[col]
        self.grid[row][col] = player
        self.heights[col] += 1
        self.moves_made += 1

    def undo(self, col):
        self.heights[col] -= 1
        row = self.rows - 1 - self.heights[col]
        self.grid[row][col] = EMPTY
        self.moves_made -= 1

    # ---- scoring ---------------------------------------------------------- #
    def count_fours(self, player):
        """Number of connected-fours owned by `player` (the real game score)."""
        g = self.grid
        n = 0
        for w in self.windows:
            if all(g[r][c] == player for r, c in w):
                n += 1
        return n

    def scores(self):
        return self.count_fours(HUMAN), self.count_fours(AI)

    def __str__(self):
        header = " ".join(str(c + 1) for c in range(self.cols))
        rows = [" ".join(SYMBOL[v] for v in row) for row in self.grid]
        return header + "\n" + "\n".join(rows)

    def compact(self):
        """One-line representation, used when printing leaf boards."""
        return "/".join("".join(SYMBOL[v] for v in row) for row in self.grid)


# --------------------------------------------------------------------------- #
#  Terminal value (heuristics live in heuristics.py, behind the
#  `Heuristic` interface)
# --------------------------------------------------------------------------- #
def terminal_value(board):
    """Exact value of a full board: (computer fours - human fours) * big."""
    hu, ai = board.scores()
    return (ai - hu) * TERMINAL_MULT


# --------------------------------------------------------------------------- #
#  Minimax with alpha-beta pruning (+ tree recording)
# --------------------------------------------------------------------------- #
class Node:
    """One node of the minimax tree (only built when printing is enabled)."""
    __slots__ = ("col", "kind", "value", "alpha", "beta",
                 "children", "pruned", "board_str", "leaf_kind")

    def __init__(self, col, kind):
        self.col = col            # move that led here (None for root)
        self.kind = kind          # "MAX" or "MIN"
        self.value = None
        self.alpha = None         # alpha/beta values on ENTRY to the node
        self.beta = None
        self.children = []
        self.pruned = 0           # number of siblings skipped by a cut-off
        self.board_str = None
        self.leaf_kind = None     # "heuristic" | "terminal" | None


class Searcher:
    def __init__(self, k, use_pruning=True, build_tree=True, keep_boards=False,
                 heuristic=None):
        self.k = k
        # any object implementing the Heuristic interface (or a name string)
        if heuristic is None:
            heuristic = DEFAULT_HEURISTIC
        if isinstance(heuristic, str):
            heuristic = get_heuristic(heuristic)
        self.heuristic = heuristic
        self.use_pruning = use_pruning
        self.build_tree = build_tree
        self.keep_boards = keep_boards
        self.nodes = 0            # nodes expanded / visited

    def best_move(self, board):
        """Run the search on `board` (computer to move). Returns (col, value, root)."""
        self.nodes = 0
        root = Node(None, "MAX") if self.build_tree else None
        value, col = self._max(board, self.k, -INF, INF, root)
        return col, value, root

    # -- helpers to attach leaf info ------------------------------------- #
    def _leaf(self, board, node, kind, value):
        if node is not None:
            node.value = value
            node.leaf_kind = kind
            if self.keep_boards:
                node.board_str = board.compact()
        return value

    def _max(self, board, depth, alpha, beta, node):
        self.nodes += 1
        if node is not None:
            node.alpha, node.beta = alpha, beta
        if board.is_full():
            return self._leaf(board, node, "terminal", terminal_value(board)), None
        if depth == 0:
            return self._leaf(board, node, "heuristic", self.heuristic.evaluate(board)), None

        best, best_col = -INF, None
        moves = board.valid_moves()
        for i, col in enumerate(moves):
            board.drop(col, AI)
            child = Node(col, "MIN") if node is not None else None
            val, _ = self._min(board, depth - 1, alpha, beta, child)
            board.undo(col)
            if node is not None:
                node.children.append(child)
            if val > best:
                best, best_col = val, col
            if self.use_pruning:
                alpha = max(alpha, best)
                if alpha >= beta:
                    if node is not None:
                        node.pruned = len(moves) - i - 1
                    break
        if node is not None:
            node.value = best
        return best, best_col

    def _min(self, board, depth, alpha, beta, node):
        self.nodes += 1
        if node is not None:
            node.alpha, node.beta = alpha, beta
        if board.is_full():
            return self._leaf(board, node, "terminal", terminal_value(board)), None
        if depth == 0:
            return self._leaf(board, node, "heuristic", self.heuristic.evaluate(board)), None

        best, best_col = INF, None
        moves = board.valid_moves()
        for i, col in enumerate(moves):
            board.drop(col, HUMAN)
            child = Node(col, "MAX") if node is not None else None
            val, _ = self._max(board, depth - 1, alpha, beta, child)
            board.undo(col)
            if node is not None:
                node.children.append(child)
            if val < best:
                best, best_col = val, col
            if self.use_pruning:
                beta = min(beta, best)
                if alpha >= beta:
                    if node is not None:
                        node.pruned = len(moves) - i - 1
                    break
        if node is not None:
            node.value = best
        return best, best_col


# --------------------------------------------------------------------------- #
#  Tree printing
# --------------------------------------------------------------------------- #
def fmt(x):
    if x == INF:
        return "+inf"
    if x == -INF:
        return "-inf"
    return str(int(x)) if float(x).is_integer() else f"{x:.1f}"


def tree_lines(root):
    """Readable, traceable text version of the minimax tree (iterative DFS)."""
    out = []

    def rec(node, prefix, is_last, depth):
        if node.col is None:
            label = "ROOT"
            branch = ""
        else:
            label = f"col {node.col + 1}"
            branch = prefix + ("└─ " if is_last else "├─ ")
        if node.leaf_kind == "heuristic":
            body = f"{label} [{node.kind}] LEAF h={fmt(node.value)}"
        elif node.leaf_kind == "terminal":
            body = f"{label} [{node.kind}] FULL-BOARD score={fmt(node.value)}"
        else:
            body = (f"{label} [{node.kind}] a={fmt(node.alpha)} b={fmt(node.beta)}"
                    f" -> {fmt(node.value)}")
        out.append(branch + body)
        child_prefix = prefix + ("   " if is_last else "│  ") if node.col is not None else ""
        if node.board_str:
            out.append(child_prefix + "   board: " + node.board_str)
        for i, ch in enumerate(node.children):
            last = (i == len(node.children) - 1) and node.pruned == 0
            rec(ch, child_prefix, last, depth + 1)
        if node.pruned:
            out.append(child_prefix + f"└─ ✂ pruned {node.pruned} remaining move(s) (alpha >= beta)")

    sys.setrecursionlimit(10000)
    rec(root, "", True, 0)
    return out


# --------------------------------------------------------------------------- #
#  Console game
# --------------------------------------------------------------------------- #
def read_human_move(board):
    while True:
        try:
            raw = input(f"Your move (column 1-{board.cols}): ").strip()
        except EOFError:
            print("\nInput closed. Exiting.")
            sys.exit(0)
        if raw.lower() in ("q", "quit", "exit"):
            print("Bye!")
            sys.exit(0)
        if not raw.isdigit():
            print("  Please enter a column number.")
            continue
        col = int(raw) - 1
        if not 0 <= col < board.cols:
            print(f"  Column must be between 1 and {board.cols}.")
        elif board.heights[col] >= board.rows:
            print("  That column is full, pick another.")
        else:
            return col


def play(args):
    board = Board(args.rows, args.cols)
    searcher = Searcher(args.k, use_pruning=True,
                        build_tree=not args.no_tree or bool(args.tree_file),
                        keep_boards=args.leaf_boards, heuristic=args.heuristic)
    tree_out = open(args.tree_file, "w", encoding="utf-8") if args.tree_file else None

    print(f"\n=== Connect 4: Human (X) vs Computer (O) | board {args.rows}x{args.cols} | K={args.k} ===")
    print(f"Heuristic: {searcher.heuristic.name} - {searcher.heuristic.description}")
    print("The game ends when the board is full; most connected-fours wins.\n")
    turn = HUMAN if args.first == "human" else AI
    turn_no = 0

    while not board.is_full():
        print(board, "\n")
        if turn == HUMAN:
            col = read_human_move(board)
            board.drop(col, HUMAN)
            print(f"You played column {col + 1}.\n")
        else:
            turn_no += 1
            t0 = time.perf_counter()
            col, value, root = searcher.best_move(board)
            dt = time.perf_counter() - t0
            if root is not None:
                lines = tree_lines(root)
                header = (f"--- Minimax tree, computer move #{turn_no} "
                          f"(K={args.k}, alpha-beta) ---")
                if not args.no_tree:
                    print(header)
                    print("\n".join(lines))
                if tree_out:
                    tree_out.write(header + "\n" + "\n".join(lines) + "\n\n")
            board.drop(col, AI)
            print(f"Computer plays column {col + 1}  "
                  f"(minimax value {fmt(value)}, nodes expanded {searcher.nodes}, "
                  f"time {dt:.3f}s)\n")
        turn = AI if turn == HUMAN else HUMAN
        hu, ai = board.scores()
        print(f"Score -> You: {hu} | Computer: {ai}\n")

    print(board, "\n")
    hu, ai = board.scores()
    print("=== Board full ===")
    print(f"Final score -> You: {hu} | Computer: {ai}")
    print("You win!" if hu > ai else "Computer wins!" if ai > hu else "It's a draw!")
    if tree_out:
        tree_out.close()


def main():
    p = argparse.ArgumentParser(description="Connect 4 - Human vs minimax/alpha-beta AI")
    p.add_argument("--k", type=int, help="search depth K (number of levels)")
    p.add_argument("--rows", type=int, default=6)
    p.add_argument("--cols", type=int, default=7)
    p.add_argument("--first", choices=["human", "ai"], default="human")
    p.add_argument("--heuristic", choices=sorted(HEURISTICS), default=DEFAULT_HEURISTIC,
                   help="evaluation function used at depth K (default: %(default)s)")
    p.add_argument("--no-tree", action="store_true", help="do not print the tree to the console")
    p.add_argument("--tree-file", help="also write every minimax tree to this file")
    p.add_argument("--leaf-boards", action="store_true",
                   help="print the board under every leaf in the tree")
    args = p.parse_args()

    if args.k is None:                       # K is a required game parameter
        while True:
            try:
                args.k = int(input("Enter K (search depth, e.g. 4): "))
                if args.k >= 1:
                    break
            except ValueError:
                pass
            print("  K must be a positive integer.")
    if args.rows < 6 or args.cols < 7:
        p.error("dimensions must satisfy width >= 7 and length >= 6")
    play(args)


if __name__ == "__main__":
    main()
