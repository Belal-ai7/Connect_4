"""Shared board values and terminal scoring for Connect 4."""

EMPTY = 0
AI = 1
HUMAN = 2

# Keep the display consistent with the game header: human is X, computer is O.
SYMBOL = {
    EMPTY: ".",
    AI: "O",
    HUMAN: "X",
}

# Ensure an exact terminal result outweighs any non-terminal heuristic score.
TERMINAL_MULT = 100_000
