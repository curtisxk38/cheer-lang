from cheer import scanner


def test_scanner():
    rules = [
        scanner.SymbolRule("def", "function def"), 
        scanner.SymbolRule("[a-zA-z]+", "id"),
        scanner.SymbolRule("[ \n]", "whitespace", add_symbol=False)
    ]
    lines = ["def asdf", "popo asdf def defdef"]
    tokens = scanner.scan(lines, rules)
    expected = [
        scanner.Symbol("function def", "def", None, 1, 1),
        scanner.Symbol("id", "asdf", None, 1, 5),
        scanner.Symbol("id", "popo", None, 2, 1),
        scanner.Symbol("id", "asdf", None, 2, 6),
        scanner.Symbol("function def", "def", None, 2, 11),
        scanner.Symbol("id", "defdef", None, 2, 15),
    ]

    assert expected == tokens

def test_scanner_to_value():
    rules = [
        scanner.SymbolRule(r"true|false", "bool_literal", to_value=lambda x: x == "true"),
        scanner.SymbolRule("[ \n]", "whitespace", add_symbol=False)
    ]

    source = ["true false       true"]
    tokens = scanner.scan(source, rules)
    print(tokens)
    expected = [
        scanner.Symbol("bool_literal", "true", True, 1, 1),
        scanner.Symbol("bool_literal", "false", False, 1, 6),
        scanner.Symbol("bool_literal", "true", True, 1, 18),
    ]

    assert expected == tokens