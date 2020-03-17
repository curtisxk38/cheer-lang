
class DFSVisitor:
    def __init__(self, ast):
        self.ast = ast
        self.methods = dir(self)

    def accept(self):
        self.visit_node(self.ast)

    def visit_node(self, node):
        in_node_name = "_in_{}".format(node.ntype)
        out_node_name = "_out_{}".format(node.ntype)
        if in_node_name in self.methods:
            getattr(self, in_node_name)(node)
        else:
            self.default_in_visit(node)
        for child in node.children:
            self.visit_node(child)
        if out_node_name in self.methods:
            getattr(self, out_node_name)(node)
        else:
            self.default_out_visit(node)

    def default_in_visit(self, node):
        print("Entering {}".format(node))

    def default_out_visit(self, node):
        print("Exiting {}".format(node))
