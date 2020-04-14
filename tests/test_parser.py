import pytest
from cheer import ast, scanner, parser, lexing_rules


def test_parse1():
    prog = ["3 * (2 + 8) - 9 * 11;"]
    tokens = scanner.scan(prog, lexing_rules.RULES)
    p = parser.Parser(tokens)
    root = p.expr()

    a3 = ast.ASTNode("int_literal", scanner.Symbol("int literal", "3", 3, 1, 1), None)
    a2 = ast.ASTNode("int_literal", scanner.Symbol("int literal", "2", 2, 1, 6), None)
    a8 = ast.ASTNode("int_literal", scanner.Symbol("int literal", "8", 8, 1, 10), None)
    a9 = ast.ASTNode("int_literal", scanner.Symbol("int literal", "9", 9, 1, 15), None)
    a11 = ast.ASTNode("int_literal", scanner.Symbol("int literal", "11", 11, 1, 19), None)

    plus = ast.ASTNode("plus_exp", scanner.Symbol("plus", "+", None, 1,  8), [a2, a8])
    times1 = ast.ASTNode("times_exp", scanner.Symbol("times", "*", None, 1,  3), [a3, plus])
    times2 = ast.ASTNode("times_exp", scanner.Symbol("times", "*", None, 1,  17), [a9, a11])
    minus = ast.ASTNode("minus_exp", scanner.Symbol("minus", "-", None, 1,  13), [times1, times2])

    assert root == minus