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
    SymbolRule(";", "semicolon"),

    
    SymbolRule("[a-zA-z]+", "id"),
    SymbolRule("[ \t\n]", "whitespace", add_symbol=False)
]