"""
catscript lexer.

Turns source text into a list of tokens, e.g.
    cat("hi")  ->  KEYWORD(cat) LPAREN STRING(hi) RPAREN
"""

import random

KEYWORDS = {
    # output / input
    "cat", "pspsps",
    # control flow
    "if", "else", "for", "in", "to", "repeat",
    # functions
    "hunt", "bring",
    # values
    "purr", "hiss", "empty_bowl", "litter",
    # misc
    "nap", "knock", "try", "pounce",
    # logic
    "and", "or", "not",
}

# this is a cat household
DOG_WORDS = {"fetch", "bark", "goodboy", "woof", "sit", "wag"}

# two-character symbols must be checked before one-character ones
SYMBOLS = {
    "==": "EQ", "!=": "NEQ", "<=": "LTE", ">=": "GTE",
    "+": "PLUS", "-": "MINUS", "*": "STAR", "/": "SLASH", "%": "PERCENT",
    "<": "LT", ">": "GT", "=": "ASSIGN",
    "(": "LPAREN", ")": "RPAREN",
    "{": "LBRACE", "}": "RBRACE",
    "[": "LBRACKET", "]": "RBRACKET",
    ",": "COMMA",
}

INSULTS = [
    "even tuft could write better code, and he has no thumbs.",
    "i've seen hairballs with better structure.",
    "did you write this while walking across the keyboard?",
    "this code is why i knock things off tables.",
    "i'm going back to sleep. fix this first.",
]


class CatError(Exception):
    """A cat-themed error with a code, a location, and an insult."""

    def __init__(self, code, message, line=None, col=None):
        self.code = code
        self.message = message
        self.line = line
        self.col = col
        super().__init__(message)

    def where(self):
        if self.line is None:
            return ""
        if self.col is None:
            return f" (line {self.line})"
        return f" (line {self.line}, col {self.col})"

    def __str__(self):
        return (
            f"\n  {self.code}{self.where()}: {self.message}\n"
            f"  {random.choice(INSULTS)}\n"
        )


class Token:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        if self.value is None:
            return self.type
        return f"{self.type}({self.value!r})"


def tokenize(source):
    tokens = []
    i = 0
    line, col = 1, 1

    def advance(n=1):
        nonlocal i, line, col
        for _ in range(n):
            if i >= len(source):
                return
            if source[i] == "\n":
                line += 1
                col = 1
            else:
                col += 1
            i += 1

    while i < len(source):
        ch = source[i]

        # whitespace
        if ch in " \t\r\n":
            advance()
            continue

        # comments: # until end of line
        if ch == "#":
            while i < len(source) and source[i] != "\n":
                advance()
            continue

        start_line, start_col = line, col

        # numbers: 42, 3.14
        if ch.isdigit():
            start = i
            while i < len(source) and (source[i].isdigit() or source[i] == "."):
                advance()
            text = source[start:i]
            if text.count(".") > 1:
                raise CatError("HISS-101", f"'{text}' is not a number", start_line, start_col)
            value = float(text) if "." in text else int(text)
            tokens.append(Token("NUMBER", value, start_line, start_col))
            continue

        # strings: "hello"
        if ch == '"':
            advance()  # skip opening quote
            chars = []
            while i < len(source) and source[i] != '"':
                if source[i] == "\n":
                    raise CatError("HISS-102", "string never closed", start_line, start_col)
                if source[i] == "\\" and i + 1 < len(source):
                    nxt = source[i + 1]
                    chars.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(nxt, nxt))
                    advance(2)
                    continue
                chars.append(source[i])
                advance()
            if i >= len(source):
                raise CatError("HISS-102", "string never closed", start_line, start_col)
            advance()  # skip closing quote
            tokens.append(Token("STRING", "".join(chars), start_line, start_col))
            continue

        # names and keywords
        if ch.isalpha() or ch == "_":
            start = i
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                advance()
            word = source[start:i]
            if word.lower() in DOG_WORDS:
                raise CatError(
                    "HISS-403",
                    f"'{word}'?? this is a cat household.",
                    start_line, start_col,
                )
            if word in KEYWORDS:
                tokens.append(Token("KEYWORD", word, start_line, start_col))
            else:
                tokens.append(Token("NAME", word, start_line, start_col))
            continue

        # symbols
        two = source[i:i + 2]
        if len(two) == 2 and two in SYMBOLS:
            tokens.append(Token(SYMBOLS[two], None, start_line, start_col))
            advance(2)
            continue
        if ch in SYMBOLS:
            tokens.append(Token(SYMBOLS[ch], None, start_line, start_col))
            advance()
            continue

        raise CatError("HISS-100", f"what is '{ch}' supposed to be", start_line, start_col)

    tokens.append(Token("EOF", None, line, col))
    return tokens


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: python lexer.py file.meow")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as f:
        code = f.read()

    try:
        for tok in tokenize(code):
            print(f"{tok.line:>3}:{tok.col:<3} {tok!r}")
    except CatError as e:
        print(e)
        sys.exit(1)
