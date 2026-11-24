from heuristic_interface import Heuristic
from models import Board, Node, Option
from enums import NodeType, LeafType, CellValue

class Searcher:
    # by default it tries to minimize (finds best play) via the best_move method
    # if the goal was to maximize :
    #    we can just flip the colors of the grid and run the best_move method

    # assuming first maximizes and second minimizes
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

        if node.board.moves_made >= self.limit:
            node.kind = NodeType.LEAF
            node.leaf_kind = LeafType.HEURISTIC
            node.value = self.heuristic(node.board)
            return True
        return False
            
    def __minimize(self, node : Node):
        if self.__base_case(node):
            return
        moves = node.board.valid_moves()
        node.value = float("inf")

        for i,col in enumerate(moves):
            child_board = node.board.copy()
            child_board.drop_disk(col, CellValue.SECOND)

            child_node = Node(NodeType.MAX, child_board, node.alpha, node.beta)
            option = Option(col, child_node)
            node.children.append(option)

            self.__maximize(child_node)
            
            node.beta = min(node.beta, child_node.value)
            node.value = min(node.value, child_node.value)
            if node.value <= node.alpha: 
                # no remaining option will be better it's safe to prune
                node.pruned = len(moves) - i - 1
                break
        return

    def __maximize(self, node : Node):
        if self.__base_case(node):
            return
        moves = node.board.valid_moves()
        node.value = float("-inf")

        for i,col in enumerate(moves):
            child_board = node.board.copy()
            child_board.drop_disk(col, CellValue.FIRST)

            child_node = Node(NodeType.MAX, child_board, node.alpha, node.beta)
            option = Option(col, child_node)
            node.children.append(option)

            self.__minimize(child_node)
            
            node.alpha = max(node.alpha, child_node.value)
            node.value = max(node.value, child_node.value)
            if node.value >= node.beta: 
                # no remaining option will be better it's safe to prune
                node.pruned = len(moves) - i - 1
                break
        return

    def best_move(self, board : Board):
        pass

