import pytest
from cheer import ast, type_checker, scanner, parser, lexing_rules, symbol_table

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
    tc.scope_stack.append(symbol_table.Scope(0))
    assert tc.type_check() is True

def test_less_than_exp_valid():
    prog = ["let x = 1 < 2;"]
    par = tc_test_helper(prog)
    root = par.statement()
    tc = type_checker.TCVisitor(root)
    tc.scope_stack.append(symbol_table.Scope(0))
    assert tc.type_check() is True

def test_less_than_exp_invalid():
    prog = ["let x = false < true;"]
    par = tc_test_helper(prog)
    root = par.statement()
    tc = type_checker.TCVisitor(root)
    tc.scope_stack.append(symbol_table.Scope(0))
    with pytest.raises(type_checker.TypeCheckingError):
        tc.type_check()

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

def test_use_invalid_scope():
    prog = """
        fn main() {
            let y: i32;
            let x: i32;
            if (input() == 1) {
                let x = 2;
            }
            y = x + 0;
        }
    """
    prog = prog.split("\n")
    par = tc_test_helper(prog)
    root = par.start()
    tc = type_checker.TCVisitor(root)
    with pytest.raises(type_checker.TypeCheckingError):
        tc.type_check()

def test_valid_shadowing_scope():
    prog = """
        fn main() {
            let y: i32;
            let x = 1;
            if (input() == 1) {
                let x = 2;
                return x;
            }
            y = x * 4;
        }
    """
    prog = prog.split("\n")
    par = tc_test_helper(prog)
    root = par.start()
    tc = type_checker.TCVisitor(root)
    assert tc.type_check() is True

def test_use_parent_scope():
    prog = """
        fn main() {
            let y = 4;
            if (input() == 1) {
                y = 1;
            }
            return y;
        }
    """
    prog = prog.split("\n")
    par = tc_test_helper(prog)
    root = par.start()
    tc = type_checker.TCVisitor(root)
    assert tc.type_check() is True