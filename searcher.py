from heuristic_interface import Heuristic
from models import Board, Node
from enums import NodeType, LeafType

class Searcher:
    # by default it tries to minimize (finds best play) via the best_move method
    # if the goal was to maximize :
    #    we can just flip the colors of the grid and run the best_move method
    def __init__(self, heuristic : Heuristic, depth_limit : int):
        self.heuristic = heuristic
        self.limit = depth_limit

    # handles base case and returns true in case of node being a leaf 
    # and returns false otherwise
    def __base_case(self, node : Node, leaf_type : LeafType):
        moves = node.board.valid_moves()
        if not moves or len(moves) == 0:
            node.kind = NodeType.LEAF
            node.leaf_kind = LeafType.TERMINAL
            node.value = node.board.terminal_value()
            return True

        if node.depth >= self.limit:
            node.kind = NodeType.LEAF
            node.leaf_kind = LeafType.HEURISTIC
            node.value = self.heuristic(node.board)
            return True
        return False
            
    def __minimize(self, node : Node):
        if self.__base_case(node):
            return
        moves = node.board.valid_moves()
        

    def __maximize(self, node : Node):
        if self.__base_case(node):
            return
        moves = node.board.valid_moves()

    def best_move(self, board : Board):
        pass

