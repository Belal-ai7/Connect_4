"""Registry and factory for the available Connect 4 heuristics."""

from .positional import PositionalHeuristic
from .score import ScoreHeuristic
from .window import WindowHeuristic

REGISTRY = {cls.name: cls for cls in
            (WindowHeuristic, PositionalHeuristic, ScoreHeuristic)}
DEFAULT = WindowHeuristic.name


def get_heuristic(name=DEFAULT):
    """Create a heuristic by name (raises ValueError for unknown names)."""
    try:
        return REGISTRY[name]()
    except KeyError:
        choices = ", ".join(REGISTRY)
        raise ValueError(f"unknown heuristic '{name}'. Choose from: {choices}") from None


__all__ = ["DEFAULT", "REGISTRY", "get_heuristic", "ScoreHeuristic",
           "WindowHeuristic", "PositionalHeuristic"]
