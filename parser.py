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
        s = self.statement_list()
        self.match("right brace")
        return ast.ASTNode("main", f, [s])

    def statement(self):
        """
        S -> return E
        S -> if (E) { L }
        S -> if (E) { L } else { L }
        """
        peek = self.peek()
        if peek.token == "return":
            r = self.match("return")
            e = self.expr()
            self.match("semicolon")
            return ast.ASTNode("return_exp", r, [e])
        if peek.token == "if":
            i = self.match("if")
            self.match("left paren")
            e = self.expr()
            self.match("right paren")
            self.match("left brace")
            l1 = self.statement_list()
            self.match("right brace")
            l2 = None
            if self.peek().token == "else":
                self.match("else")
                self.match("left brace")
                l2 = self.statement_list()
                self.match("right brace")
            # children are:
            #  expression condition, if statement list, else statement list
            #  else statment list could be None
            return ast.ASTNode("if_else", i, [e, l1, l2])

    def statement_list(self):
        """
        L -> S L | S
        assume all statement lists must end if next token is }
        """
        statements = []
        s = self.statement()
        statements.append(s)
        while self.peek().token != "right brace":
            statements.append(self.statement())
        return ast.ASTNode("statement_list", s.symbol, statements)

    def expr(self):
        """
        E -> T
        E -> T == T
        """
        t = self.term()
        peek = self.peek()
        if peek.token == "equality":
            e = self.match("equality")
            t2 = self.term()
            return ast.ASTNode("equality_exp", e, [t, t2])
        return t
        

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
