import collections
from typing import Dict, List, Set, Tuple

from cheer import ast, gen_ir


class SymbolTableError(Exception):
    pass


class AlreadyCreatedError(SymbolTableError):
    pass


class NotDeclaredError(SymbolTableError):
    pass


class Scope:
    def __init__(self, scope_num):
        self.scope_num = scope_num

    def __hash__(self):
        return self.scope_num

    def __eq__(self, other):
        return self.scope_num == other.scope_num

    def __repr__(self):
        return str(f"Scope<{self.scope_num}>")

    def __gt__(self, other):
        return self.scope_num > other.scope_num

    def __lt__(self, other):
        return self.scope_num < other.scope_num


class STE:
    def __init__(self, node: ast.ASTNode, declared: Scope):
        self.node = node
        # set of scopes this ste was assigned in
        self.assigned_scopes: Set[Scope] = set()
        # scope this var is declared in
        self.declared_scope: Scope = declared

        # for IR gen, list of names
        # its a stack for the scopes this lexeme is used in
        # tuple of (Scope, register_name)
        self.ir_names: List[Tuple['gen_ir.BasicBlock', str]] = []

    def __repr__(self):
        return str(f"<{self.node}, Scopes: {self.assigned_scopes}>")

    def assign_in_scope(self, scope: Scope):
        self.assigned_scopes.add(scope)

    def is_assigned_in_scope(self, scope_stack: List[Scope]):
        # search through scope stack and see if its assigned in one of them
        for scope in scope_stack[::-1]:
            if scope in self.assigned_scopes:
                return True
        return False

    # used in IR gen, not type checking
    def assign_to_lexeme(self, basic_block: 'gen_ir.BasicBlock', ir_name: str):
        # if there is an entry in ir_names
        # and the most recent entry has the same bb as the parameter
        if len(self.ir_names) > 0 and self.ir_names[-1][0] == basic_block:
            # overwrite it with the new ir_name
            self.ir_names.pop()
            self.ir_names.append((basic_block, ir_name))
        else:
            # create new entry in ir_names
            self.ir_names.append((basic_block, ir_name))


class SymTable:
    def __init__(self):
        self.st: Dict[Scope, Dict[str, STE]] = collections.defaultdict(dict)

    def create(self, node: ast.ASTNode, scope_stack: List[Scope]):
        if node.ntype != "var_decl" and node.ntype != "var_decl_assign":
            raise ValueError(f"expected var type, not {node.ntype}")
        if node.symbol.lexeme in self.st:
            raise AlreadyCreatedError(f"lexeme {node.symbol} already exists in this scope")

        ste = STE(node, scope_stack[-1])
        self.st[scope_stack[-1]][node.symbol.lexeme] = ste
        return ste

    def get(self, node: ast.ASTNode, scope_stack: List[Scope]):
        # walk scope stack, from youngest child scope to oldest parent scope
        for scope in scope_stack[::-1]:
            try:
                return self.st[scope][node.symbol.lexeme]
            except KeyError:
                # didn't exist in that scope
                pass
        # tried all scopes in the scope stack and it wasn't in any of them
        raise NotDeclaredError(f"{node.symbol} is not declared in available scopes")

    def get_type(self, node: ast.ASTNode, scope_stack: List[Scope]):
        return self.get(node, scope_stack).node.type

    def __repr__(self):
        return str(self.st)