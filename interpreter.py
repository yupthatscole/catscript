"""
catscript interpreter.

Walks the tree from the parser and actually runs it.
"""

import time

from lexer import CatError
from parser import (
    Literal, Var, Litter, BinOp, UnaryOp, Call, Index,
    Assign, ExprStmt, If, For, Repeat, Hunt, Bring, Knock, Try,
)



# values

#   numbers     -> python int / float
#   text        -> python str
#   purr / hiss -> python True / False
#   empty_bowl  -> python None
#   litter      -> python list
#   hunt        -> CatFunction
#   built-ins   -> Builtin


def is_number(v):
    # bool counts as an int in python, but purr + 1 shouldn't work
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def kind(v):
    if v is None:
        return "empty_bowl"
    if isinstance(v, bool):
        return "purr/hiss"
    if is_number(v):
        return "number"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "litter"
    return "hunt"


def show(v, inside=False):
    """How a value looks when cat() prints it."""
    if v is None:
        return "empty_bowl"
    if v is True:
        return "purr"
    if v is False:
        return "hiss"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, str):
        return f'"{v}"' if inside else v
    if isinstance(v, list):
        return "litter[" + ", ".join(show(x, inside=True) for x in v) + "]"
    return str(v)


def truthy(v):
    if v is None or v is False:
        return False
    if is_number(v):
        return v != 0
    if isinstance(v, (str, list)):
        return len(v) > 0
    return True


def as_whole_number(v, what, line):
    if is_number(v) and float(v).is_integer():
        return int(v)
    raise CatError("HISS-300", f"{what} has to be a whole number, not {show(v, True)}", line)


class CatFunction:
    def __init__(self, node, closure):
        self.node = node
        self.closure = closure

    def __str__(self):
        return f"<hunt {self.node.name}>"


class Builtin:
    def __init__(self, name, fn):
        self.name = name
        self.fn = fn

    def __str__(self):
        return f"<built-in {self.name}>"


class BringSignal(Exception):
    """Thrown by 'bring' to jump out of a hunt with a value."""

    def __init__(self, value):
        self.value = value




class Env:
    def __init__(self, parent=None):
        self.vars = {}
        self.parent = parent

    def find(self, name):
        env = self
        while env is not None:
            if name in env.vars:
                return env
            env = env.parent
        return None

    def get(self, name, line):
        env = self.find(name)
        if env is None:
            raise CatError("HISS-404", f"never heard of '{name}'. did you make it up?", line)
        return env.vars[name]

    def set(self, name, value):
        env = self.find(name) or self
        env.vars[name] = value

    def define(self, name, value):
        self.vars[name] = value

    def delete(self, name, line):
        env = self.find(name)
        if env is None:
            raise CatError("HISS-404", f"can't knock '{name}' off the table, it was never there", line)
        del env.vars[name]




def check_args(name, args, low, high, line):
    if not (low <= len(args) <= high):
        want = str(low) if low == high else f"{low} to {high}"
        raise CatError("HISS-406", f"{name}() wants {want} things, you gave it {len(args)}", line)


def b_cat(args, line):
    print(" ".join(show(a) for a in args))
    return None


def b_pspsps(args, line):
    check_args("pspsps", args, 0, 1, line)
    prompt = show(args[0]) if args else ""
    answer = input(prompt)
    # if they typed a number, give back a number
    try:
        return int(answer)
    except ValueError:
        pass
    try:
        return float(answer)
    except ValueError:
        return answer


def b_nap(args, line):
    check_args("nap", args, 1, 1, line)
    if not is_number(args[0]) or args[0] < 0:
        raise CatError("HISS-300", "nap() needs a number of seconds", line)
    time.sleep(args[0])
    return None


def b_size(args, line):
    check_args("size", args, 1, 1, line)
    v = args[0]
    if not isinstance(v, (str, list)):
        raise CatError("HISS-300", f"a {kind(v)} doesn't have a size", line)
    return len(v)


def b_add(args, line):
    check_args("add", args, 2, 2, line)
    if not isinstance(args[0], list):
        raise CatError("HISS-300", f"you can only add kittens to a litter, not a {kind(args[0])}", line)
    args[0].append(args[1])
    return None


def b_text(args, line):
    check_args("text", args, 1, 1, line)
    return show(args[0])


BUILTINS = {
    "cat": b_cat,
    "pspsps": b_pspsps,
    "nap": b_nap,
    "size": b_size,
    "add": b_add,
    "text": b_text,
}


class Interpreter:
    def __init__(self):
        self.globals = Env()
        for name, fn in BUILTINS.items():
            self.globals.define(name, Builtin(name, fn))

    def run(self, statements):
        try:
            self.exec_block(statements, self.globals)
        except BringSignal:
            raise CatError("HISS-409", "you can only 'bring' inside a hunt")

    def exec_block(self, statements, env):
        for stmt in statements:
            self.execute(stmt, env)

    # --- statements -----------------------------------------------------

    def execute(self, node, env):
        method = getattr(self, "exec_" + type(node).__name__)
        method(node, env)

    def exec_ExprStmt(self, node, env):
        self.evaluate(node.expr, env)

    def exec_Assign(self, node, env):
        value = self.evaluate(node.value, env)
        target = node.target
        if isinstance(target, Var):
            if target.name in BUILTINS and env.find(target.name) is self.globals:
                raise CatError("HISS-403", f"'{target.name}' is taken. find your own name", node.line)
            env.set(target.name, value)
        else:  # Index
            container = self.evaluate(target.target, env)
            if not isinstance(container, list):
                raise CatError("HISS-300", f"you can only change slots in a litter, not a {kind(container)}", node.line)
            i = self.index_of(container, self.evaluate(target.index, env), node.line)
            container[i] = value

    def exec_If(self, node, env):
        if truthy(self.evaluate(node.cond, env)):
            self.exec_block(node.then, env)
        elif node.otherwise is not None:
            self.exec_block(node.otherwise, env)

    def exec_For(self, node, env):
        start = as_whole_number(self.evaluate(node.start, env), "the start of a for loop", node.line)
        end = as_whole_number(self.evaluate(node.end, env), "the end of a for loop", node.line)
        step = 1 if end >= start else -1
        for i in range(start, end + step, step):
            env.set(node.var, i)
            self.exec_block(node.body, env)

    def exec_Repeat(self, node, env):
        count = as_whole_number(self.evaluate(node.count, env), "repeat", node.line)
        for _ in range(count):
            self.exec_block(node.body, env)

    def exec_Hunt(self, node, env):
        env.set(node.name, CatFunction(node, env))

    def exec_Bring(self, node, env):
        value = None if node.value is None else self.evaluate(node.value, env)
        raise BringSignal(value)

    def exec_Knock(self, node, env):
        env.delete(node.name, node.line)

    def exec_Try(self, node, env):
        try:
            self.exec_block(node.body, env)
        except CatError as e:
            if node.err_name:
                env.set(node.err_name, f"{e.code}: {e.message}")
            self.exec_block(node.handler, env)

  

    def evaluate(self, node, env):
        method = getattr(self, "eval_" + type(node).__name__)
        return method(node, env)

    def eval_Literal(self, node, env):
        return node.value

    def eval_Var(self, node, env):
        return env.get(node.name, node.line)

    def eval_Litter(self, node, env):
        return [self.evaluate(item, env) for item in node.items]

    def eval_UnaryOp(self, node, env):
        v = self.evaluate(node.operand, env)
        if node.op == "not":
            return not truthy(v)
        if not is_number(v):
            raise CatError("HISS-300", f"can't make a {kind(v)} negative", node.line)
        return -v

    def eval_BinOp(self, node, env):
        op = node.op

        # and / or only look at the right side if they need to
        if op == "and":
            left = self.evaluate(node.left, env)
            return self.evaluate(node.right, env) if truthy(left) else left
        if op == "or":
            left = self.evaluate(node.left, env)
            return left if truthy(left) else self.evaluate(node.right, env)

        a = self.evaluate(node.left, env)
        b = self.evaluate(node.right, env)

        if op == "==":
            return a == b and kind(a) == kind(b)
        if op == "!=":
            return not (a == b and kind(a) == kind(b))

        if op == "+":
            if is_number(a) and is_number(b):
                return a + b
            if isinstance(a, str) or isinstance(b, str):
                return show(a) + show(b)        # "lives: " + 9 works
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            raise CatError("HISS-300", f"can't add a {kind(a)} and a {kind(b)}", node.line)

        if op == "*" and isinstance(a, str) and is_number(b):
            return a * as_whole_number(b, "text repeat count", node.line)

        if op in ("<", ">", "<=", ">="):
            same = (is_number(a) and is_number(b)) or (isinstance(a, str) and isinstance(b, str))
            if not same:
                raise CatError("HISS-300", f"can't compare a {kind(a)} with a {kind(b)}", node.line)
            return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]

        # - * / % need two numbers
        if not (is_number(a) and is_number(b)):
            raise CatError("HISS-300", f"can't do {kind(a)} {op} {kind(b)}", node.line)
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if b == 0:
            raise CatError("HISS-500", "you can't split the fish into zero pieces", node.line)
        if op == "/":
            result = a / b
            return int(result) if result.is_integer() else result
        if op == "%":
            return a % b

        raise CatError("HISS-999", f"unknown operator {op}", node.line)

    def index_of(self, container, index, line):
        i = as_whole_number(index, "a litter position", line)
        n = len(container)
        if not -n <= i < n:
            raise CatError("HISS-416", f"there's no kitten at position {i}, the litter only has {n}", line)
        return i

    def eval_Index(self, node, env):
        container = self.evaluate(node.target, env)
        if not isinstance(container, (list, str)):
            raise CatError("HISS-300", f"can't look inside a {kind(container)} with []", node.line)
        i = self.index_of(container, self.evaluate(node.index, env), node.line)
        return container[i]

    def eval_Call(self, node, env):
        callee = self.evaluate(node.callee, env)
        args = [self.evaluate(a, env) for a in node.args]

        if isinstance(callee, Builtin):
            return callee.fn(args, node.line)

        if isinstance(callee, CatFunction):
            params = callee.node.params
            if len(args) != len(params):
                raise CatError(
                    "HISS-406",
                    f"{callee.node.name}() wants {len(params)} things, you gave it {len(args)}",
                    node.line,
                )
            local = Env(callee.closure)
            for name, value in zip(params, args):
                local.define(name, value)
            try:
                self.exec_block(callee.node.body, local)
            except BringSignal as b:
                return b.value
            return None

        raise CatError("HISS-405", f"you can't call a {kind(callee)} like a hunt", node.line)
