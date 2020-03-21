from cheer import visit


class TCVisitor(visit.DFSVisitor):
    def __init__(self, ast):
        super().__init__(ast)
        self.symbol_table = []

    def error(self, msg):
        raise TypeError(msg)

    def type_check(self):
        self.accept()

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass

    def _out_int_literal(self, node):
        node.type = "i32"

    def _out_bool_literal(self, node):
        node.type = "bool"

    def _out_var_decl(self, node):
        node.type = node.children[0].symbol.lexeme

    def _out_var_decl_assign(self, node):
        node.type = node.children[0].type

    # assumes children nodes should have matching types
    def op_helper(self, node, valid_types):
        t = node.children[0].type
        if valid_types and t not in valid_types:
            msg = f"Expected {c1} to have one of types: {valid_types}"
            self.error(msg)
            return None
        for c in node.children[1:]:
            if c.type != t:
                msg = f"Expected {c} ({c.type}) to have type {t}"
                self.error(msg)
                return None
        return t

    def _out_plus_exp(self, node):
        t = self.op_helper(node, ["i32"])
        node.type = t

    def _out_minus_exp(self, node):
        t = self.op_helper(node, ["i32"])
        node.type = t

    def _out_times_exp(self, node):
        t = self.op_helper(node, ["i32"])
        node.type = t

    def _out_equality_exp(self, node):
        _ = self.op_helper(node, None)
        node.type = "bool"
