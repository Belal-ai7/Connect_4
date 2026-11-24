from enum import Enum

class NodeType(Enum):
    MAX = 1
    MIN = 2
    LEAF = 3

class LeafType(Enum):
    TERMINAL = 1
    HEURISTIC = 2
    
class Symbol(Enum):
    EMPTY = "."
    AI = "O"
    HUMAN = "X"

class CellValue(Enum):
    EMPTY = 0
    AI = 1
    HUMAN = 2

