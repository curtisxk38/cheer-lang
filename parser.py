from typing import List

import scanner
import ast


class Parser:
    def __init__(self, tokens: List[scanner.Symbol]):
        self.tokens = tokens
        self.tokens.append(scanner.Symbol("EOF", "$", -1, -1, -1))

    def peek(self):
        return self.tokens[0]

    def error(self, e):
        print(e)

    def start(self):
        root = self.fn()

        if self.peek().token != "EOF":
            self.error(f"Expected end of file, got {self.peek()}")

        return root

    def match(self, token):
        peek = self.peek()
        if peek.token == token:
            self.tokens = self.tokens[1:]
            return peek
        else:
            self.error(f"Expected {token}, saw {peek}")

    def fn(self):
        self.match("function def")
        f = self.match("id")
        self.match("left paren")
        self.match("right paren")
        self.match("left brace")
        e = self.expr()
        self.match("right brace")
        return ast.ASTNode("main", f, [e])



    def expr(self):
        if self.peek().token == "int literal":
            sym = self.match("int literal")
            return ast.ASTNode("int literal", sym, None)

if __name__ == "__main__":
    from lexing_rules import RULES
    import sys
    fname = sys.argv[1]
    with open(fname) as f:
        symbols = scanner.scan(f, RULES)

    p = Parser(symbols)
    root = p.start()
    print(ast.gen_ast_digraph(root))
