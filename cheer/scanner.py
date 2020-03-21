import re


class SymbolRule:
    def __init__(self, re, token_name, to_value=lambda _: -1, add_symbol=True):
        self.re = re
        self.token_name = token_name
        self.to_value = to_value
        self.add_symbol = add_symbol


class Symbol:
    def __init__(self, token, lexeme, value, line, col):
        self.token = token # ex: function def, int literal, if, etc...
        self.lexeme = lexeme # what was in the source code
        self.value = value # value, ex token "5" has value 5
        self.line = line # line number
        self.col = col # column number

    def __repr__(self):
        return "{}<{}> at ({},{})".format(self.token, self.lexeme, self.line, self.col)

    def location(self):
        return f"({self.line}, {self.col}"

    def __eq__(self, other):
        if not isinstance(other, Symbol):
            return False
        return (self.token, self.lexeme, self.value, self.line, self.col) == \
            (other.token, other.lexeme, other.value, other.line, other.col)

    def __hash__(self):
        return hash( (self.token, self.lexeme, self.value, self.line, self.col) )

def scan(f_iter, rules):
    """
    won't be able to scan tokens that are multiline tokens
    """
    symbols = []

    for _line_num, line in enumerate(f_iter):
        line_num = _line_num + 1
        col_num = 1
        while len(line) > 0:
            # remember which regular expression matched the longest string
            max_match_len = 0
            max_symbol = None

            for rule in rules:
                m = re.match(rule.re, line)
                if m is not None:
                    lexeme = m.group()
                    if len(lexeme) > max_match_len:
                        max_match_len = len(lexeme)
                        symbol = None
                        if rule.add_symbol:
                            symbol = Symbol(rule.token_name, lexeme, rule.to_value(lexeme), line_num, col_num)
                        max_symbol = symbol

            if max_match_len == 0:
                raise ValueError(f"No match found for {line} ({line_num}, {col_num})")
            
            if max_symbol is not None:
                symbols.append(max_symbol)
            col_num += max_match_len
            line = line[max_match_len:]

    return symbols

def dummy_tokenize(input_str):
    """
    turn a string into a list of dummy symbols
    need list of symbols to parse
    """
    return [Symbol(char, char, -1, -1, -1) for char in list(input_str)]

def main():
    rules = [
        SymbolRule(r"true|false", "bool_literal", to_value=lambda x: x == "true"),
        SymbolRule("[ \n]", "whitespace", add_symbol=False)
    ]

    source = ["true false       true"]
    tokens = scan(source, rules)


if __name__ == "__main__":
    main()