#!/usr/bin/env python3
"""
Head-to-head tournament between heuristics.

Each pair plays two full games (board filled completely), once with each
heuristic moving first, using the same depth K for both sides. The winner is
decided by the number of connected-fours, exactly as in the assignment.

    python compare_heuristics.py            # K = 3
    python compare_heuristics.py 4
"""
import itertools
import sys
import time

from connect4 import Board, Searcher
from constants import AI, HUMAN
from heuristic_implementations import REGISTRY


def flipped(board):
    """Copy of the board with the two colours swapped, so the same
    'computer = AI' searcher can also play the other side."""
    b = board.copy()
    swap = {0: 0, HUMAN: AI, AI: HUMAN}
    b.grid = [[swap[v] for v in row] for row in board.grid]
    return b


def play_game(first, second, k):
    """`first` plays as HUMAN-coloured side, `second` as AI-coloured side.
    Returns (first_fours, second_fours)."""
    board = Board()
    s_first = Searcher(k, build_tree=False, heuristic=first)
    s_second = Searcher(k, build_tree=False, heuristic=second)
    turn = HUMAN
    while not board.is_full():
        if turn == AI:
            col, _, _ = s_second.best_move(board)
            board.drop(col, AI)
        else:
            col, _, _ = s_first.best_move(flipped(board))
            board.drop(col, HUMAN)
        turn = AI if turn == HUMAN else HUMAN
    h, a = board.scores()
    return h, a


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    names = sorted(REGISTRY)
    wins = {n: 0 for n in names}
    fours = {n: 0 for n in names}
    print(f"Tournament, K={k}, board 6x7, played to a full board\n")
    print("| Moves first | Moves second | Fours (first) | Fours (second) | Winner |")
    print("|---|---|---:|---:|---|")
    t0 = time.perf_counter()
    for a, b in itertools.permutations(names, 2):
        fa, fb = play_game(a, b, k)
        fours[a] += fa
        fours[b] += fb
        if fa > fb:
            w = a; wins[a] += 1
        elif fb > fa:
            w = b; wins[b] += 1
        else:
            w = "draw"
        print(f"| {a} | {b} | {fa} | {fb} | {w} |")
    print(f"\n(total time {time.perf_counter() - t0:.1f}s)\n")
    print("| Heuristic | Wins | Total fours |")
    print("|---|---:|---:|")
    for n in sorted(names, key=lambda n: (-wins[n], -fours[n])):
        print(f"| {n} | {wins[n]} | {fours[n]} |")


if __name__ == "__main__":
    main()
