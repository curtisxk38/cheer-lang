from typing import List, Dict
import collections

from cheer import scanner

class ASTNode:
    def __init__(self, ntype: str, symbol: scanner.Symbol, children: List['ASTNode']):
        self.ntype = ntype # node type
        self.symbol = symbol
        self.children = children or []
        self.parent = None

        for c in self.children:
            c.parent = self

def gen_ast_digraph(root: ASTNode):
    """
    generate diagram for ast rooted at this node
    """
    counter = 0
    node_to_id: Dict[ASTNode, int] = {}
    digraph = "digraph G {\n"
    unexamined: collections.deque = collections.deque()
    unexamined.append(root)
    digraph += "\t\"\" [shape=none];\n"
    while len(unexamined) > 0:
        look_at = unexamined.popleft()
        if look_at not in node_to_id:
            node_to_id[look_at] = counter
            digraph += "\t{} [ label=\"{}\" ];\n".format(counter, look_at.ntype)
            counter += 1
        # for root
        if look_at.parent is None:
            digraph += "\t\"\" -> {};\n".format(node_to_id[look_at])
        else:
            digraph += "\t{} -> {};\n".format(node_to_id[look_at.parent], node_to_id[look_at])
        unexamined.extend(look_at.children)
    digraph += "}"
    return digraph
