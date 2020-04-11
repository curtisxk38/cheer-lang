import collections
from typing import Dict

from cheer import ast


class AlreadyCreatedError(Exception):
    pass


class Scope:
    def __init__(self, scope_num):
        self.scope_num = scope_num

    def __hash__(self):
        return hash(self.scope_num)


class STE:
    def __init__(self, node, been_assigned):
        self.node = node
        self.been_assigned = been_assigned;
        self.scope = 0

        # for IR gen
        self.reg_num = 0
        self.ir_name = ""

    # name of SSA IR var
    def get_ssa_new_name(self):
        return f"{self.node.lexeme}.{self.scope}.{self.reg_num}"

class SymTable:
    def __init__(self):
        self.scope = 1
        self.st: Dict[Scope, Dict[str, STE]] = collections.defaultdict(dict)

    def create(self, node: ast.ASTNode, scope: Scope, been_assigned=False):
        if node.ntype != "var_decl" and node.ntype != "var_decl_assign":
            raise ValueError(f"expected var type, not {node.ntype}")
        if node.symbol.lexeme in self.st:
            raise AlreadyCreatedError(f"lexeme {node.symbol.lexeme} already exists in this scope")

        self.st[scope][node.symbol.lexeme] = STE(node, been_assigned)

    def get(self, node: ast.ASTNode, scope: Scope):
        return self.st[scope][node.symbol.lexeme]

    def get_type(self, node: ast.ASTNode, scope: Scope):
        return self.get(node, scope).node.type