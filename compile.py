from lexing_rules import RULES
import scanner
import parser
import sys
import gen_ir

def main(fname):
    with open(fname) as f:
        symbols = scanner.scan(f, RULES)

    p = parser.Parser(symbols)
    ast_root = p.start()

    gen_code = gen_ir.CodeGenVisitor(ast_root)
    gen_code.accept()
    with open(fname + ".ll", "w") as outfile:
        outfile.write(gen_code.get_code())


if __name__ == "__main__":
    main(sys.argv[1])
    