from cheer import ast

from typing import Dict


class AlreadyCreatedError(Exception):
    pass


class STE:
    def __init__(self, node):
        self.node = node


class SymTable:
    def __init__(self):
        self.scope = 1
        self.st: Dict[str, STE] = {}

    def create(self, node: ast.ASTNode):
        if node.ntype != "var_decl" and node.ntype != "var_decl_assign":
            raise ValueError(f"expected var type, not {node.ntype}")
        if node.symbol.lexeme in self.st:
            raise AlreadyCreatedError(f"lexeme {node.symbol.lexeme} already exists in this scope")

        self.st[node.symbol.lexeme] = STE(node)

    def get(self, node: str):
        return self.st[node].node.type