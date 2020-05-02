import argparse
import os

from cheer.lexing_rules import RULES
from cheer import scanner
from cheer import parser
from cheer import gen_ir
from cheer import ast
from cheer import type_checker

def compile(options, lines):
    symbols = scanner.scan(lines, RULES)

    p = parser.Parser(symbols)
    ast_root = p.start()

    if options.verbose:
        print(ast.gen_ast_digraph(ast_root))

    tc = type_checker.TCVisitor(ast_root)
    tc.type_check()

    gen_code = gen_ir.CodeGenVisitor(ast_root, tc.symbol_table)
    gen_code.accept()
    return gen_code.get_code()

def main(options):
    with open(options.input) as f:
        code = compile(options, f)

    oname = options.output
    if oname is None:
        oname = os.path.splitext(options.input)[0] + ".ll"

    with open(oname, "w") as outfile:
        outfile.write(code)


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
