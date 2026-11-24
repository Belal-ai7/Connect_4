from enum import Enum

class NodeType(Enum):
    MAX = 1
    MIN = 2
    LEAF = 3

class LeafType(Enum):
    TERMINAL = 1
    HEURISTIC = 2

class CellValue(Enum):
    EMPTY = 0
    FIRST = 1
    SECOND = 2

