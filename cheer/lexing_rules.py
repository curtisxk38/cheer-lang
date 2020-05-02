from cheer.scanner import SymbolRule

RULES = [
    SymbolRule("fn", "function def"),
    SymbolRule("[0-9]+", "int literal", to_value=lambda x: int(x)),
    SymbolRule("\(", "left paren"),
    SymbolRule("\)", "right paren"),
    SymbolRule("{", "left brace"),
    SymbolRule("}", "right brace"),
    SymbolRule("\+", "plus"),
    SymbolRule("-", "minus"),
    SymbolRule("\*", "times"),
    SymbolRule("return", "return"),
    SymbolRule("input", "input"),
    SymbolRule("if", "if"),
    SymbolRule("else", "else"),
    SymbolRule("==", "equality"),
    SymbolRule("<", "left angle bracket"),
    SymbolRule(">", "right angle bracket"),
    SymbolRule(";", "semicolon"),
    SymbolRule("let", "let"),
    SymbolRule("=", "assign"),
    SymbolRule(":", "colon"),
    SymbolRule("i32", "i32"),
    SymbolRule("bool", "bool"),
    SymbolRule(r"true|false", "bool_literal", to_value=lambda x: x == "true"),
    SymbolRule("while", "while"),
    
    SymbolRule(r"[a-zA-z][\w]*", "id"),
    SymbolRule("[ \t\n]", "whitespace", add_symbol=False)
]