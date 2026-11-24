"""Small Flask frontend for the Connect 4 minimax agent."""

from uuid import uuid4
from math import isinf

from flask import Flask, flash, redirect, render_template, request, session, url_for

from connect4_game.enums import CellValue
from connect4_game.heuristic_implementations import DEFAULT, REGISTRY, get_heuristic
from connect4_game.models import Board
from connect4_game.searcher import Searcher

app = Flask(__name__)
app.secret_key = "connect4-local-development-key"
TREE_CACHE = {}
DEFAULT_DEPTH = 3


def make_board(saved=None):
    """Create an empty board or restore one from session data."""
    if not saved:
        return Board()
    board = Board(len(saved["grid"]), len(saved["grid"][0]))
    board.grid = [[CellValue(value) for value in row] for row in saved["grid"]]
    board.heights = saved["heights"]
    board.moves_made = saved["moves_made"]
    return board


def save_game(board, depth, heuristic_name, game_over=False):
    """Persist only the current board and game settings in the session."""
    session["game"] = {
        "grid": [[cell.value for cell in row] for row in board.grid],
        "heights": board.heights,
        "moves_made": board.moves_made,
        "depth": depth,
        "heuristic": heuristic_name,
        "game_over": game_over,
    }
    session.setdefault("game_id", str(uuid4()))


def swap_players(board):
    """Copy a board with FIRST and SECOND exchanged for AI search."""
    flipped = board.copy()
    swap = {
        CellValue.EMPTY: CellValue.EMPTY,
        CellValue.FIRST: CellValue.SECOND,
        CellValue.SECOND: CellValue.FIRST,
    }
    flipped.grid = [[swap[cell] for cell in row] for row in board.grid]
    return flipped


def tree_to_data(node):
    """Convert search nodes to template-friendly dictionaries."""
    def display_value(value):
        if value is None:
            return None
        if isinstance(value, (int, float)) and isinf(value):
            return "-∞" if value < 0 else "+∞"
        return value

    return {
        "kind": node.kind.name,
        "value": display_value(node.value),
        "alpha": display_value(node.alpha),
        "beta": display_value(node.beta),
        "leaf_kind": node.leaf_kind.name if node.leaf_kind else None,
        "pruned": node.pruned,
        "children": [
            {"column": option.pos + 1, "node": tree_to_data(option.target)}
            for option in node.children
        ],
    }


def choose_ai_move(board, depth, heuristic_name):
    """Search from the AI's perspective and return its move and search tree."""
    searcher = Searcher(get_heuristic(heuristic_name), depth)
    column, root = searcher.best_move(swap_players(board))
    return column, tree_to_data(root)


def game_result(board):
    """Return a human-readable result once the board is full."""
    human_score, ai_score = board.scores()
    if human_score == ai_score:
        return f"Draw ({human_score} fours each)."
    winner = "You win" if human_score > ai_score else "AI wins"
    return f"{winner}: you {human_score}, AI {ai_score} fours."


@app.get("/")
def index():
    """Show the current game, board, and most recent AI search tree."""
    game = session.get("game")
    board = make_board(game)
    tree = TREE_CACHE.get(session.get("game_id"))
    return render_template(
        "index.html",
        board=board,
        game=game,
        tree=tree,
        heuristics=REGISTRY,
        result=game_result(board) if game and game["game_over"] else None,
    )


@app.post("/new")
def new_game():
    """Start a new empty game with the selected settings."""
    try:
        depth = int(request.form.get("depth", DEFAULT_DEPTH))
        if not 1 <= depth <= 8:
            raise ValueError
        heuristic_name = request.form.get("heuristic", DEFAULT)
        if heuristic_name not in REGISTRY:
            raise ValueError
    except ValueError:
        flash("Choose a depth from 1 to 8 and a listed heuristic.")
        return redirect(url_for("index"))

    old_id = session.get("game_id")
    if old_id:
        TREE_CACHE.pop(old_id, None)
    session.pop("game_id", None)
    save_game(Board(), depth, heuristic_name)
    return redirect(url_for("index"))


@app.post("/move")
def play_move():
    """Apply the human move, search for the AI reply, and retain its tree."""
    game = session.get("game")
    if not game or game["game_over"]:
        flash("Start a new game before playing.")
        return redirect(url_for("index"))

    board = make_board(game)
    try:
        column = int(request.form["column"])
        board.drop_disk(column, CellValue.FIRST)
    except (KeyError, ValueError):
        flash("Choose a column that is not full.")
        return redirect(url_for("index"))

    if board.is_full():
        save_game(board, game["depth"], game["heuristic"], game_over=True)
        return redirect(url_for("index"))

    ai_column, tree = choose_ai_move(board, game["depth"], game["heuristic"])
    board.drop_disk(ai_column, CellValue.SECOND)
    save_game(board, game["depth"], game["heuristic"], game_over=board.is_full())
    TREE_CACHE[session["game_id"]] = tree
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
