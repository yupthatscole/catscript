"""
catscript parser.

Turns the flat list of tokens from the lexer into a tree (an AST).
For example:

    cat(1 + 2 * 3)

becomes

    Call(Var("cat"), [BinOp("+", 1, BinOp("*", 2, 3))])

so the interpreter knows to do 2 * 3 before the + .
"""

from dataclasses import dataclass

from lexer import CatError, SYMBOLS

# reverse lookup so error messages can say "}" instead of "RBRACE"
SYMBOL_TEXT = {name: text for text, name in SYMBOLS.items()}

# keywords that act like functions you can call
BUILTIN_KEYWORDS = {"cat", "pspsps", "nap"}



# tree nodes: expressions (things that produce a value)


@dataclass
class Literal:        # 42, "hi", purr, hiss, empty_bowl
    value: object
    line: int


@dataclass
class Var:            # a name like x or kittens
    name: str
    line: int


@dataclass
class Litter:         # litter[1, 2, 3]
    items: list
    line: int


@dataclass
class BinOp:          # a + b, a == b, a and b, ...
    op: str
    left: object
    right: object
    line: int


@dataclass
class UnaryOp:        # -x, not x
    op: str
    operand: object
    line: int


@dataclass
class Call:           # double(5), cat("hi")
    callee: object
    args: list
    line: int


@dataclass
class Index:          # kittens[0]
    target: object
    index: object
    line: int


# tree nodes: statements (things that do something)


@dataclass
class Assign:         # x = 5, kittens[0] = 9
    target: object
    value: object
    line: int


@dataclass
class ExprStmt:       # an expression on its own line, like cat("hi")
    expr: object
    line: int


@dataclass
class If:
    cond: object
    then: list
    otherwise: list   # None if there's no else
    line: int


@dataclass
class For:            # for i in 1 to 10 { ... }
    var: str
    start: object
    end: object
    body: list
    line: int


@dataclass
class Repeat:         # repeat 3 { ... }
    count: object
    body: list
    line: int


@dataclass
class Hunt:           # hunt double(x) { ... }
    name: str
    params: list
    body: list
    line: int


@dataclass
class Bring:          # bring x * 2
    value: object
    line: int


@dataclass
class Knock:          # knock(x)
    name: str
    line: int


@dataclass
class Try:            # try { ... } pounce err { ... }
    body: list
    err_name: str     # None if they didn't name the error
    handler: list
    line: int



# the parser


def describe(tok):
    """How a token looks in an error message."""
    if tok.type == "EOF":
        return "the end of the file"
    if tok.type == "STRING":
        return f'"{tok.value}"'
    if tok.value is not None:
        return f"'{tok.value}'"
    return f"'{SYMBOL_TEXT.get(tok.type, tok.type)}'"


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

  

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        tok = self.tokens[self.pos]
        if tok.type != "EOF":
            self.pos += 1
        return tok

    def check(self, type, value=None):
        tok = self.peek()
        return tok.type == type and (value is None or tok.value == value)

    def match(self, type, value=None):
        if self.check(type, value):
            return self.advance()
        return None

    def expect(self, type, value=None):
        if self.check(type, value):
            return self.advance()
        tok = self.peek()
        if value is not None:
            want = f"'{value}'"
        elif type == "NAME":
            want = "a name"
        else:
            want = f"'{SYMBOL_TEXT.get(type, type)}'"
        raise CatError(
            "HISS-200",
            f"expected {want} but found {describe(tok)}",
            tok.line, tok.col,
        )

    def fail(self, code, message, tok=None):
        tok = tok or self.peek()
        raise CatError(code, message, tok.line, tok.col)



    def parse_program(self):
        statements = []
        while not self.check("EOF"):
            statements.append(self.parse_statement())
        return statements

    def parse_block(self):
        opener = self.expect("LBRACE")
        statements = []
        while not self.check("RBRACE"):
            if self.check("EOF"):
                self.fail(
                    "HISS-201",
                    f"you never closed the {{ from line {opener.line}",
                    opener,
                )
            statements.append(self.parse_statement())
        self.expect("RBRACE")
        return statements

   

    def parse_statement(self):
        tok = self.peek()

        if tok.type == "KEYWORD":
            if tok.value == "if":
                return self.parse_if()
            if tok.value == "for":
                return self.parse_for()
            if tok.value == "repeat":
                return self.parse_repeat()
            if tok.value == "hunt":
                return self.parse_hunt()
            if tok.value == "bring":
                return self.parse_bring()
            if tok.value == "try":
                return self.parse_try()
            if tok.value == "knock":
                return self.parse_knock()
            if tok.value == "else":
                self.fail("HISS-202", "'else' with no 'if' before it")
            if tok.value == "pounce":
                self.fail("HISS-202", "'pounce' with no 'try' before it")

        if tok.type == "RBRACE":
            self.fail("HISS-201", "this } doesn't close anything")

        expr = self.parse_expression()

        if self.match("ASSIGN"):
            if not isinstance(expr, (Var, Index)):
                self.fail("HISS-203", "you can only put values into names or litter slots", tok)
            value = self.parse_expression()
            return Assign(expr, value, tok.line)

        return ExprStmt(expr, tok.line)

    def parse_if(self):
        line = self.advance().line            # 'if'
        cond = self.parse_expression()
        then = self.parse_block()
        otherwise = None
        if self.match("KEYWORD", "else"):
            if self.check("KEYWORD", "if"):
                otherwise = [self.parse_if()]  # else if ... is just an if inside the else
            else:
                otherwise = self.parse_block()
        return If(cond, then, otherwise, line)

    def parse_for(self):
        line = self.advance().line            # 'for'
        name = self.expect("NAME").value
        self.expect("KEYWORD", "in")
        start = self.parse_expression()
        self.expect("KEYWORD", "to")
        end = self.parse_expression()
        body = self.parse_block()
        return For(name, start, end, body, line)

    def parse_repeat(self):
        line = self.advance().line            # 'repeat'
        count = self.parse_expression()
        body = self.parse_block()
        return Repeat(count, body, line)

    def parse_hunt(self):
        line = self.advance().line            # 'hunt'
        name = self.expect("NAME").value
        self.expect("LPAREN")
        params = []
        if not self.check("RPAREN"):
            params.append(self.expect("NAME").value)
            while self.match("COMMA"):
                params.append(self.expect("NAME").value)
        self.expect("RPAREN")
        body = self.parse_block()
        return Hunt(name, params, body, line)

    def parse_bring(self):
        line = self.advance().line            # 'bring'
        if self.check("RBRACE"):
            return Bring(None, line)          # bring with nothing = bring empty_bowl
        return Bring(self.parse_expression(), line)

    def parse_try(self):
        line = self.advance().line            # 'try'
        body = self.parse_block()
        self.expect("KEYWORD", "pounce")
        err_name = None
        if self.check("NAME"):
            err_name = self.advance().value
        handler = self.parse_block()
        return Try(body, err_name, handler, line)

    def parse_knock(self):
        line = self.advance().line            # 'knock'
        self.expect("LPAREN")
        name = self.expect("NAME").value
        self.expect("RPAREN")
        return Knock(name, line)

    # expressions, lowest priority first 
    #   or  ->  and  ->  not  ->  == < >  ->  + -  ->  * / %  ->  -x  ->  calls/[]  ->  values

    def parse_expression(self):
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.check("KEYWORD", "or"):
            line = self.advance().line
            left = BinOp("or", left, self.parse_and(), line)
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.check("KEYWORD", "and"):
            line = self.advance().line
            left = BinOp("and", left, self.parse_not(), line)
        return left

    def parse_not(self):
        if self.check("KEYWORD", "not"):
            line = self.advance().line
            return UnaryOp("not", self.parse_not(), line)
        return self.parse_comparison()

    COMPARE = {"EQ": "==", "NEQ": "!=", "LT": "<", "GT": ">", "LTE": "<=", "GTE": ">="}
    ADD = {"PLUS": "+", "MINUS": "-"}
    MULTIPLY = {"STAR": "*", "SLASH": "/", "PERCENT": "%"}

    def parse_comparison(self):
        left = self.parse_additive()
        while self.peek().type in self.COMPARE:
            tok = self.advance()
            left = BinOp(self.COMPARE[tok.type], left, self.parse_additive(), tok.line)
        return left

    def parse_additive(self):
        left = self.parse_multiplicative()
        while self.peek().type in self.ADD:
            tok = self.advance()
            left = BinOp(self.ADD[tok.type], left, self.parse_multiplicative(), tok.line)
        return left

    def parse_multiplicative(self):
        left = self.parse_unary()
        while self.peek().type in self.MULTIPLY:
            tok = self.advance()
            left = BinOp(self.MULTIPLY[tok.type], left, self.parse_unary(), tok.line)
        return left

    def parse_unary(self):
        if self.check("MINUS"):
            line = self.advance().line
            return UnaryOp("-", self.parse_unary(), line)
        return self.parse_postfix()

    def parse_postfix(self):
        expr = self.parse_primary()
        while True:
            if self.check("LPAREN"):
                line = self.advance().line
                args = []
                if not self.check("RPAREN"):
                    args.append(self.parse_expression())
                    while self.match("COMMA"):
                        args.append(self.parse_expression())
                self.expect("RPAREN")
                expr = Call(expr, args, line)
            elif self.check("LBRACKET"):
                line = self.advance().line
                index = self.parse_expression()
                self.expect("RBRACKET")
                expr = Index(expr, index, line)
            else:
                return expr

    def parse_primary(self):
        tok = self.peek()

        if tok.type in ("NUMBER", "STRING"):
            self.advance()
            return Literal(tok.value, tok.line)

        if tok.type == "NAME":
            self.advance()
            return Var(tok.value, tok.line)

        if tok.type == "KEYWORD":
            if tok.value == "purr":
                self.advance()
                return Literal(True, tok.line)
            if tok.value == "hiss":
                self.advance()
                return Literal(False, tok.line)
            if tok.value == "empty_bowl":
                self.advance()
                return Literal(None, tok.line)
            if tok.value == "litter":
                self.advance()
                self.expect("LBRACKET")
                items = []
                if not self.check("RBRACKET"):
                    items.append(self.parse_expression())
                    while self.match("COMMA"):
                        items.append(self.parse_expression())
                self.expect("RBRACKET")
                return Litter(items, tok.line)
            if tok.value in BUILTIN_KEYWORDS:
                self.advance()
                return Var(tok.value, tok.line)

        if tok.type == "LPAREN":
            self.advance()
            expr = self.parse_expression()
            self.expect("RPAREN")
            return expr

        self.fail("HISS-200", f"expected a value but found {describe(tok)}")


def parse(tokens):
    return Parser(tokens).parse_program()
