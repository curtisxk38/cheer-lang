from typing import List
from cheer import visit
from cheer import symbol_table


class TypeCheckingError(Exception):
    pass


class TCVisitor(visit.DFSVisitor):
    def __init__(self, ast):
        super().__init__(ast)
        self.symbol_table = symbol_table.SymTable()
        self.scope_num = 0
        self.scope_stack: List[symbol_table.Scope] = []

    def error(self, msg):
        raise TypeCheckingError(msg)

    def type_check(self):
        self.accept()
        return True

    def default_in_visit(self, node):
        # override
        pass

    def default_out_visit(self, node):
        # override
        pass

    def _in_statement_list(self, node):
        new_scope = symbol_table.Scope(self.scope_num)
        self.scope_num += 1
        self.scope_stack.append(new_scope)

    def _out_statement_list(self, node):
        self.scope_stack.pop()

    def _out_int_literal(self, node):
        node.type = "i32"

    def _out_bool_literal(self, node):
        node.type = "bool"

    def _out_var(self, node):
        try:
            node.type = self.symbol_table.get_type(node, self.scope_stack)
        except symbol_table.NotDeclaredError:
            msg = f"Use of variable {node.symbol.lexeme} before declaration\n"
            msg += f"{node.symbol}"
            self.error(msg)

        if not self.symbol_table.get(node, self.scope_stack).is_assigned_in_scope(self.scope_stack):
            msg = f"Use of variable {node.symbol.lexeme} before assignment\n"
            msg += f"{node.symbol}"
            self.error(msg)

    def _out_input_exp(self, node):
        node.type = "i32";

    def _out_var_decl(self, node):
        node.type = node.children[0].symbol.lexeme
        self.symbol_table.create(node, self.scope_stack)

    def _out_var_decl_assign(self, node):
        node.type = node.children[0].type
        ste = self.symbol_table.create(node, self.scope_stack)
        ste.assign_in_scope(self.scope_stack[-1])

    def _visit_assignment(self, node):
        """
        Because of the weird way we parse assignment statements
        we only want to visit the rhs of the =, not the lhs
        thats why we're overriding _visit instead of _out
        """
        # visit rhs (expression)
        self.visit_node(node.children[1])
        
        lhs = node.children[0]
        try:
            t = self.symbol_table.get_type(lhs, self.scope_stack)
        except symbol_table.NotDeclaredError:
            msg = f"Assignment to variable {lhs.symbol.lexeme} before declaration\n"
            msg += f"{lhs.symbol}"
            self.error(msg)
        if t != node.children[1].type:
            msg = f"Assignment to {lhs.symbol.lexeme} should be {t} not {node.children[1].type}"
            self.error(msg)

        self.symbol_table.get(lhs, self.scope_stack).assign_in_scope(self.scope_stack[-1])

    # assumes children nodes should have matching types
    def op_helper(self, node, valid_types):
        t = node.children[0].type
        if valid_types and t not in valid_types:
            msg = f"Expected {node.children[0]} ({t}) to have one of types: {valid_types}"
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
