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
        """
        E -> return T
        """
        r = self.match("return")
        e = self.term()
        return ast.ASTNode("return_exp", r, [e])

    def term(self):
        """
        T -> F | F + T | F - T 
        """
        left = self.factor()
        peek = self.peek()
        if peek.token == "plus":
            plus = self.match("plus")
            right = self.term()
            return ast.ASTNode("plus_exp", plus, [left, right])
        elif peek.token == "minus":
            minus = self.match("minus")
            right = self.term()
            return ast.ASTNode("minus_exp", minus, [left, right])

        return left

    def factor(self):
        """
        F -> P | P * F
        """
        left = self.paren()
        peek = self.peek()
        if peek.token == "times":
            times = self.match("times")
            right = self.factor()
            return ast.ASTNode("times_exp", times, [left, right])

        return left

    def paren(self):
        """
        P -> I | (E)
        """
        peek = self.peek()
        if peek.token == "left paren":
            self.match("left paren")
            ex = self.term()
            self.match("right paren")
            return ex
        elif peek.token == "int literal":
            return self.int_literal()
        elif peek.token == "input":
            i = self.match("input")
            self.match("left paren")
            self.match("right paren")
            return ast.ASTNode("input_exp", i, None)

    def int_literal(self):
        sym = self.match("int literal")
        return ast.ASTNode("int_literal", sym, None)
            

if __name__ == "__main__":
    from lexing_rules import RULES
    import sys
    fname = sys.argv[1]
    with open(fname) as f:
        symbols = scanner.scan(f, RULES)

    p = Parser(symbols)
    root = p.start()
    print(ast.gen_ast_digraph(root))
