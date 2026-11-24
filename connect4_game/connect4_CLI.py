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

from .enums import *
from .heuristic_interface import Heuristic
from .heuristic_implementations import DEFAULT as DEFAULT_HEURISTIC
from .heuristic_implementations import REGISTRY as HEURISTICS
from .heuristic_implementations import get_heuristic





INF = float("inf")

# --------------------------------------------------------------------------- #
#  Terminal value (heuristics live in heuristics.py, behind the
#  `Heuristic` interface)
# --------------------------------------------------------------------------- #

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
    pass
    

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
