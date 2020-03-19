import argparse
import os

from cheer.lexing_rules import RULES
from cheer import scanner
from cheer import parser
from cheer import sys
from cheer import gen_ir
from cheer import ast

def main(parsed):
    with open(parsed.input) as f:
        symbols = scanner.scan(f, RULES)

    p = parser.Parser(symbols)
    ast_root = p.start()

    if parsed.verbose:
        print(ast.gen_ast_digraph(ast_root))

    gen_code = gen_ir.CodeGenVisitor(ast_root)
    gen_code.accept()


    oname = parsed.output
    if oname is None:
        oname = os.path.splitext(parsed.input)[0] + ".ll"  

    with open(oname, "w") as outfile:
        outfile.write(gen_code.get_code())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument('--input', '-i', required=True,
        help='Cheer file to compile')

    ap.add_argument('--output', '-o',
        help='Filename of output ll file')

    ap.add_argument('--verbose', '-v', action='store_true',
        help='Print verbose output')

    parsed = ap.parse_args()

    main(parsed)
    