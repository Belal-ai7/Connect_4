from .heuristic_interface import Heuristic
from .models import Board, Node, Option
from .enums import NodeType, LeafType, CellValue

class Searcher:
    # by default it tries to maximize (finds best play) via the best_move method
    # if the goal was to minimize :
    #    we can just flip the colors of the grid and run the best_move method

    # assuming first maximizes and second minimizes
    def __init__(self, heuristic : Heuristic, depth_limit : int):
        if depth_limit < 1:
            raise ValueError("depth_limit must be at least 1")
        self.heuristic = heuristic
        self.limit = depth_limit

    # handles base case and returns true in case of node being a leaf 
    # and returns false otherwise
    def __base_case(self, node : Node):
        moves = node.board.valid_moves()
        if not moves:
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
        node.subtree_nodes = 1
        moves = node.board.valid_moves()
        node.value = float("inf")

        for i,col in enumerate(moves):
            child_board = node.board.copy()
            child_board.drop_disk(col, CellValue.SECOND)

            child_node = Node(NodeType.MAX, child_board, 
                              node.depth + 1, 
                              node.alpha, node.beta)
            option = Option(col, child_node)
            node.children.append(option)

            self.__maximize(child_node)
            node.subtree_nodes += child_node.subtree_nodes
            
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
        node.subtree_nodes = 1
        moves = node.board.valid_moves()
        node.value = float("-inf")

        for i,col in enumerate(moves):
            child_board = node.board.copy()
            child_board.drop_disk(col, CellValue.FIRST)

            child_node = Node(NodeType.MIN, child_board, 
                              node.depth + 1, 
                              node.alpha, node.beta)
            option = Option(col, child_node)
            node.children.append(option)

            self.__minimize(child_node)
            node.subtree_nodes += child_node.subtree_nodes
            
            node.alpha = max(node.alpha, child_node.value)
            node.value = max(node.value, child_node.value)
            if node.value >= node.beta: 
                # no remaining option will be better it's safe to prune
                node.pruned = len(moves) - i - 1
                break
        return

    # gets the best move based on the Searcher's heuristic (maximization by default) 
    # and returns the root node of the minimax tree
    def best_move(self, board : Board) -> tuple[int, Node]:
        if not board.valid_moves():
            raise ValueError("cannot choose a move on a full board")

        node = Node(NodeType.MAX, board)
        self.__maximize(node)
        best_option = 0
        best_res = float("-inf")

        for option in node.children:
            if option.target.value > best_res:
                best_option = option.pos
                best_res = option.target.value

        return best_option, node



