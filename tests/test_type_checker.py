import pytest
from cheer import ast, type_checker, scanner, parser, lexing_rules

def tc_test_helper(prog):
    tokens = scanner.scan(prog, lexing_rules.RULES)
    p = parser.Parser(tokens)
    return p
    

def test_plus_exp_invalid():
    prog = ["return true + 1;"]
    par = tc_test_helper(prog)
    root = par.statement()
    tc = type_checker.TCVisitor(root)
    with pytest.raises(type_checker.TypeCheckingError):
        tc.type_check()

def test_plus_exp_valid():
    prog = ["let x = 1 + 2;"]
    par = tc_test_helper(prog)
    root = par.statement()
    tc = type_checker.TCVisitor(root)
    assert tc.type_check() is True

def test_use_before_assign():
    prog = """
        fn main() {
            let y: i32;
            if (input() == 1) {
                y = 2;
            } else {
                return 0;
            }
            return y;
        }
    """
    prog = prog.split("\n")
    par = tc_test_helper(prog)
    root = par.start()
    tc = type_checker.TCVisitor(root)
    with pytest.raises(type_checker.TypeCheckingError):
        tc.type_check()