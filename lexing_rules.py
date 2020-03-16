from scanner import SymbolRule

RULES = [
    SymbolRule("fn", "function def"),
    SymbolRule("[0-9]+", "int literal", to_value=lambda x: int(x)),
    SymbolRule("\(", "left paren"),
    SymbolRule("\)", "right paren"),
    SymbolRule("{", "left brace"),
    SymbolRule("}", "right brace"),
    SymbolRule("[a-zA-z]+", "id"),
    SymbolRule("\+", "plus"),
    SymbolRule("-", "minus"),
    SymbolRule("\*", "times"),
    SymbolRule("[ \t\n]", "whitespace", add_symbol=False)
]