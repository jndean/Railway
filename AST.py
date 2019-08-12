from fractions import Fraction


def BINOP_ADD(a, b):
    return a + b
def BINOP_SUB(a, b):
    return a - b
def BINOP_MUL(a, b):
    return a * b
def BINOP_DIV(a, b):
    return a / b
def BINOP_POW(a, b):
    return Fraction(a ** b)
def BINOP_IDIV(a, b):
    return Fraction(a // b)
def BINOP_MOD(a, b):
    return a % b
def BINOP_XOR(a, b):
    return Fraction(bool(a) ^ bool(b))
def BINOP_OR(a, b):
    return Fraction(bool(a) | bool(b))
def BINOP_AND(a, b):
    return Fraction(bool(a) & bool(b))
def BINOP_LESS(a, b):
    return Fraction(a < b)
def BINOP_LEQ(a, b):
    return Fraction(a <= b)
def BINOP_GREAT(a, b):
    return Fraction(a > b)
def BINOP_GEQ(a, b):
    return Fraction(a >= b)
def BINOP_EQ(a, b):
    return Fraction(a == b)
def BINOP_NEQ(a, b):
    return Fraction(a != b)
def UNIOP_NOT(a):
    return Fraction(not a)
def UNIOP_SUB(a):
    return -a


class Binop:
    __slots__ = ["lhs", "op", "rhs"]

    def __new__(cls, lhs, op_token, rhs):
        # Optimise away constants
        if isinstance(lhs, Fraction) and isinstance(rhs, Fraction):
            op = globals()["BINOP_" + op_token]
            return op(lhs, rhs)
        return super().__new__(cls)

    def __init__(self, lhs, op_token, rhs):
        self.lhs = lhs
        self.op = globals()["BINOP_" + op_token]
        self.rhs = rhs


class Uniop:
    __slots__ = ["op", "expr"]

    def __new__(cls, op_token, expr):
        # Optimise away constants
        if isinstance(expr, Fraction):
            op = globals()["UNIOP_" + op_token]
            return op(expr)
        return super().__new__(cls)

    def __init__(self, op_token, expr):
        self.op = globals()["UNIOP_" + op_token]
        self.expr = expr


class Variable:
    __slots__ = ["name", "index", "ismono"]

    def __init__(self, name, index, ismono):
        self.name = name
        self.index = index
        self.ismono = ismono


class Parameter:
    __slots__ = ["name", "isborrowed", "ismono"]

    def __init__(self, name, isborrowed, ismono):
        self.name = name
        self.isborrowed = isborrowed
        self.ismono = ismono


class Length:
    __slots__ = ["variable"]

    def __init__(self, variable):
        self.variable = variable


class Let:
    __slots__ = ["variable", "rhs"]

    def __init__(self, variable, rhs):
        self.variable = variable
        self.rhs = rhs


class Unlet:
    __slots__ = ["variable", "rhs"]

    def __init__(self, variable, rhs):
        self.variable = variable
        self.rhs = rhs


class Statements:
    __slots__ = ["items", "isswitch"]

    def __init__(self, items):
        self.items = items
        self.isswitch = any(hasattr(x, "isswitch") and x.isswitch
                            for x in items)


class Function:
    __slots__ = ["name", "isswitch", "parameters", "lines", "retname"]

    def __init__(self, name, isswitch, parameters, lines, retname):
        self.name = name
        self.isswitch = isswitch
        self.parameters = parameters
        self.lines = lines
        self.retname = retname


class Module:
    __slots__ = ['functions']

    def __init__(self, functions):
        self.functions = functions


"""class ArrayGen():
    __slots__ = ["start_expr", "end_expr", "step_expr",
                 "subarray", "name", "expr"]

    def __init__(self, start_expr=None, end_expr=None, step_expr=None,
                 subarray=None, name=None, expr=None):
        self.generator = generator
        def gen(name, expr)
"""


def display(node, indent=0):
    start = ' |' * indent + '->'
    indent += 1

    if isinstance(node, Fraction):
        print(start, str(node))

    elif isinstance(node, Binop):
        print(start, node.op.__name__)
        display(node.lhs, indent)
        display(node.rhs, indent)

    elif isinstance(node, Uniop):
        print(start, node.op.__name__)
        display(node.expr, indent)

    elif isinstance(node, Variable):
        print(start, node.name + '[]' * len(node.index),
              "(ismono)" if node.ismono else "")
        for idx in node.index:
            display(idx, indent)

    elif isinstance(node, Parameter):
        out = '@' if node.isborrowed else ''
        out += '.'if node.ismono else ''
        out += node.name
        print(start, out)

    elif isinstance(node, Length):
        print(start, "Length")
        display(node.variable, indent)

    elif isinstance(node, Let) or isinstance(node, Unlet):
        print(start, type(node).__name__)
        display(node.variable, indent)
        display(node.rhs, indent)

    elif isinstance(node, list):
        for elt in node:
            display(elt, indent-1)

    elif isinstance(node, Function):
        print(start, "func", node.name)
        display(node.parameters, indent+1)
        display(node.lines, indent+1)
        print(start, "return", node.retname)

    elif isinstance(node, Module):
        display(node.functions, indent)
