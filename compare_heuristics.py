#!/usr/bin/env python3
"""
Fair head-to-head tournament between Connect 4 heuristics.

Fairness measures:
  * Parity fix: each role gets a fresh heuristic instance whose
    ai_moves_first flag matches the role it plays.
  * Shared random openings: each opening (2-4 random legal moves) is played
    once with each heuristic moving first, so both sides face the same
    starting positions.
  * Draws are counted and reported, not dropped.
  * The first-mover win rate is reported as a sanity check.

Usage:
    python compare_heuristics.py              # K = 3, 10 openings per pair
    python compare_heuristics.py 4            # K = 4, 10 openings per pair
    python compare_heuristics.py 4 20         # K = 4, 20 openings per pair
"""

import copy
import itertools
import random
import sys
import time

from connect4 import Board, Searcher
from constants import AI, HUMAN
from heuristic_implementations import REGISTRY

OPENING_MIN = 2
OPENING_MAX = 4


def flipped(board):
    """Copy of the board with the two colours swapped, so the same
    'computer = AI' searcher can also play the other side."""
    b = board.copy()
    swap = {0: 0, HUMAN: AI, AI: HUMAN}
    b.grid = [[swap[v] for v in row] for row in board.grid]
    return b


def make_heuristic(name, ai_moves_first):
    """Fresh heuristic instance whose parity flag matches its role."""
    proto = REGISTRY[name]
    h = proto() if isinstance(proto, type) else copy.copy(proto)
    if hasattr(h, "ai_moves_first"):
        h.ai_moves_first = ai_moves_first
    return h


def random_opening(seed):
    """Return a list of column indices: a short random opening.

    Discs alternate starting with HUMAN colour. The seed makes the opening
    reproducible, and the same opening is reused for both move orders.
    """
    rng = random.Random(seed)
    length = rng.randint(OPENING_MIN, OPENING_MAX)
    board = Board()
    moves = []
    for i in range(length):
        legal = [c for c in range(board.cols) if board.heights[c] < board.rows]
        col = rng.choice(legal)
        board.drop(col, HUMAN if i % 2 == 0 else AI)
        moves.append(col)
    return moves


def play_game(first_name, second_name, k, opening):
    """Play one game from the given opening.

    first_name is the heuristic that moves first (HUMAN colour in the
    opening sequence), second_name moves second (AI colour).
    Returns (first_fours, second_fours).
    """
    board = Board()
    for i, col in enumerate(opening):
        board.drop(col, HUMAN if i % 2 == 0 else AI)

    # Whoever moves next depends on how many opening discs were placed.
    turn = HUMAN if len(opening) % 2 == 0 else AI

    # The first mover sees the board through flipped(), so its own discs
    # are AI and ai_moves_first is True. The second mover is the real AI
    # and moves second, so ai_moves_first is False.
    s_first = Searcher(k, build_tree=False,
                       heuristic=make_heuristic(first_name, ai_moves_first=True))
    s_second = Searcher(k, build_tree=False,
                        heuristic=make_heuristic(second_name, ai_moves_first=False))

    while not board.is_full():
        if turn == AI:
            col, _, _ = s_second.best_move(board)
            board.drop(col, AI)
        else:
            col, _, _ = s_first.best_move(flipped(board))
            board.drop(col, HUMAN)
        turn = AI if turn == HUMAN else HUMAN

    human_fours, ai_fours = board.scores()
    return human_fours, ai_fours  # (first mover, second mover)


def outcome(mine, theirs):
    """Return 'W', 'D' or 'L' from the point of view of 'mine'."""
    if mine > theirs:
        return "W"
    if mine < theirs:
        return "L"
    return "D"


def main():
    k = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    n_openings = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    names = sorted(REGISTRY)
    openings = [random_opening(seed) for seed in range(n_openings)]

    overall = {n: {"W": 0, "D": 0, "L": 0, "fours": 0} for n in names}
    first_wins = first_losses = 0  # decided games only (no draws)
    pair_rows = []

    print(f"Tournament: K={k}, board 6x7, {n_openings} openings per pair, "
          f"each opening played in both move orders, played to a full board.\n")

    t0 = time.perf_counter()
    for a, b in itertools.combinations(names, 2):
        pair = {"W": 0, "D": 0, "L": 0}  # a's record against b
        for opening in openings:
            for first, second in ((a, b), (b, a)):
                f, s = play_game(first, second, k, opening)
                fours = {first: f, second: s}

                overall[first]["fours"] += f
                overall[second]["fours"] += s

                result_a = outcome(fours[a], fours[b])
                pair[result_a] += 1
                overall[a]["W" if result_a == "W" else "L" if result_a == "L" else "D"] += 1
                overall[b]["W" if result_a == "L" else "L" if result_a == "W" else "D"] += 1

                if f > s:
                    first_wins += 1
                elif s > f:
                    first_losses += 1

        pair_rows.append((a, b, pair))

    elapsed = time.perf_counter() - t0
    games_per_heuristic = 2 * n_openings * (len(names) - 1)

    print("## Head-to-head (record of the first name)\n")
    print("| Heuristic A | Heuristic B | A W | A D | A L |")
    print("|---|---|---:|---:|---:|")
    for a, b, p in pair_rows:
        print(f"| {a} | {b} | {p['W']} | {p['D']} | {p['L']} |")

    print("\n## Overall\n")
    print("Score = wins + 0.5 * draws, as a share of games played.\n")
    print("| Heuristic | W | D | L | Score % | Total fours | Avg fours/game |")
    print("|---|---:|---:|---:|---:|---:|---:|")

    def score_key(n):
        r = overall[n]
        return -(r["W"] + 0.5 * r["D"]), -r["fours"]

    for n in sorted(names, key=score_key):
        r = overall[n]
        score_pct = 100 * (r["W"] + 0.5 * r["D"]) / games_per_heuristic
        avg = r["fours"] / games_per_heuristic
        print(f"| {n} | {r['W']} | {r['D']} | {r['L']} | {score_pct:.1f} | "
              f"{r['fours']} | {avg:.2f} |")

    decided = first_wins + first_losses
    if decided:
        print(f"\nFirst-mover win rate (decided games): "
              f"{100 * first_wins / decided:.1f}% "
              f"({first_wins} of {decided}). Should be near 50% if the openings "
              f"and heuristics are balanced.")
    print(f"\n(total time {elapsed:.1f}s)")


if __name__ == "__main__":
    main()