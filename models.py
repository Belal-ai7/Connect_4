from enums import NodeType, CellValue, Symbol

# Ensure an exact terminal result outweighs any non-terminal heuristic score.
TERMINAL_MULT = 100_000

class Board:
    """Grid stored as grid[row][col], row 0 = TOP, row ROWS-1 = BOTTOM."""

    def __init__(self, rows=6, cols=7):
        self.rows = rows
        self.cols = cols

        self.grid : list[list[Symbol]] = [[Symbol.EMPTY] * cols for _ in range(rows)]
        self.heights = [0] * cols          # discs currently in each column
        self.moves_made = 0
        # Pre-compute every window of 4 cells once (huge speed-up).
        self.windows = self._build_windows()
        # Column order: centre first -> better alpha-beta pruning.
        centre = (cols - 1) / 2
        self.col_order = sorted(range(cols), key=lambda c: (abs(c - centre), c))

    def _build_windows(self):
        wins = []
        R, C = self.rows, self.cols
        for r in range(R):
            for c in range(C):
                for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                    last_r, last_c = r + 3 * dr, c + 3 * dc
                    # only add windows having all cells within the grid
                    if 0 <= last_r < R and 0 <= last_c < C:
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

    def valid_moves(self) -> list[int]:
        return [c for c in self.col_order if self.heights[c] < self.rows]

    def drop_disk(self, col, key):
        if self.heights[col] >= self.rows:
            raise Exception("cant drop a disk into a full column")
        
        row = self.rows - self.heights[col] - 1
        self.heights[col] += 1

        self.grid[row][col] = key
        self.moves_made += 1

    def is_full(self) -> bool:
        return self.moves_made == self.rows * self.cols
    
    def count_fours(self, key) -> int:
        count = 0
        for w in self.windows:
            matches = True
            for cell in w:
                if self.grid[cell[0]][cell[1]] != key:
                    matches = False
                    break
            if matches:
                count += 1
        return count

    def scores(self) -> tuple[int,int]:
        return self.count_fours(CellValue.HUMAN), self.count_fours(Symbol.AI)

    def terminal_value(self):
        """Exact value of a full board: (computer fours - human fours) * big."""
        hu, ai = self.scores()
        return (ai - hu) * TERMINAL_MULT


    def __str__(self):
        header = " ".join(str(c + 1) for c in range(self.cols))
        rows = [" ".join(v.val for v in row) for row in self.grid]
        return header + "\n" + "\n".join(rows)


class Node:
    """One node of the minimax tree"""
    # built recursively during solution building

    def __init__(self, col, kind : NodeType, board: Board, depth : int):
        self.depth = depth        # can also be considered the round number + 1
        self.col = col            # play made in the last round to reach this state  
        self.board = board        # board after the previous play (before this round)
             
        self.kind = kind          # "MAX", "MIN" or "LEAF"
        self.value = None
        self.alpha = None         # alpha/beta values on ENTRY to the node
        self.beta = None
        
        self.children : list[Node] = []
        self.pruned = 0           # number of siblings skipped by a cut-off

        self.leaf_kind = None     # "heuristic" | "terminal" | None

