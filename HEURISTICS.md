# Heuristic Interface & Implementations

The evaluation function is now a **pluggable interface** (`heuristic_interface.py`; implementations in the `heuristic_implementations/` folder) instead of a hard-coded function. The minimax/alpha-beta search (`connect4.py`) only talks to the interface, so heuristics can be swapped with one command-line flag.

## 1. The interface

```python
class Heuristic(ABC):
    name = "..."          # id used on the command line
    description = "..."   # one-line summary

    @abstractmethod
    def evaluate(self, board) -> float:
        """Value of `board` for the COMPUTER:
           bigger  = computer nearer to winning
           smaller = human nearer to winning"""
```

* `evaluate` must not modify the board.
* Useful board members: `board.grid[row][col]` (row 0 = top), `board.heights[col]`, `board.windows` (all 69 four-cell lines), `board.rows`, `board.cols`.
* Full boards never reach the heuristic: the search returns the exact result `(computer fours − human fours) × 100000` instead (`constants.TERMINAL_MULT`).

`Searcher(k, heuristic=...)` accepts a heuristic object **or** a registered name:

```python
Searcher(4, heuristic="positional")
Searcher(4, heuristic=MyHeuristic())
```

## 2. Implementations

| Name | Idea |
|---|---|
| `window` (default) | Each four-cell window holding one colour only scores by disc count: 4 → 1000, 3 → 50, 2 → 10, 1 → 1. Mixed windows are dead (0). Centre-column discs add +3. Computer adds, human subtracts. |
| `positional` | Completed four = 1000. Each disc is worth the number of windows through its cell. A 3-disc window with an empty cell that is **playable right now** = 120 (immediate threat), not yet playable = 40. 2-disc window = 8. |
| `score` | Baseline: only the difference of completed fours (×1000). Blind to threats. |

`window` is exactly the heuristic described in `REPORT.md` section 5; the benchmark numbers there are unchanged (re-verified: K=4 → 235 nodes, value −2; K=6 → 2127 nodes, value −4).

## 3. Using it

```bash
python connect4.py --k 4                          # default: window
python connect4.py --k 4 --heuristic positional
python connect4.py --k 4 --heuristic score
python compare_heuristics.py 4                    # head-to-head tournament at depth 4
```

The chosen heuristic is printed in the game header.

## 4. Adding your own

```python
# heuristic_implementations/my_heuristic.py
class MyHeuristic(Heuristic):
    name = "mine"
    description = "what it does"

    def evaluate(self, board):
        ...                      # return a number, computer's point of view

REGISTRY = {cls.name: cls for cls in (WindowHeuristic, PositionalHeuristic,
                                      ScoreHeuristic, MyHeuristic)}
```

It then appears automatically in `--heuristic` and in `compare_heuristics.py`.

## 5. Head-to-head results (same K for both sides, games played to a full board)

Each pairing is played twice (each side moves first once). Play is deterministic, so this is **one game per ordering**: a small sample.

| K | window | positional | score |
|---|---|---|---|
| 3 | 0 wins / 14 fours | 3 wins / 21 fours | 1 win / 27 fours |
| 4 | 1 win / 8 fours | 1 win / 4 fours | 1 win / 7 fours |
| 5 | 2 wins / 21 fours | 2 wins / 18 fours | 0 wins / 20 fours |

**What this shows (and doesn't):**
* No heuristic is clearly best. Results flip with K and with who moves first, which is expected with so few games.
* `score` is weakest at K=5, but it stays competitive at K=3–4. Because the game counts *every* four until the board is full, simply grabbing fours is a strong strategy at shallow depth.
* `window` and `positional` are roughly level at K=5. A real ranking would need many more games (e.g. random openings) or a different board size.

Raw tables: `heuristic_comparison_k3.md`, `_k4.md`, `_k5.md`.

## 6. Files changed / added

| File | Change |
|---|---|
| `heuristic_interface.py` | **new** – only the abstract `Heuristic` interface |
| `heuristic_implementations.py` | **new** – the 3 implementations, registry and `get_heuristic()` |
| `constants.py` | **new** – shared constants (avoids circular import) |
| `connect4.py` | uses the interface; new `--heuristic` flag; old hard-coded function removed |
| `compare_heuristics.py` | **new** – tournament script |
