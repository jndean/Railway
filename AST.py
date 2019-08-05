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


class Binop():
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


class Uniop():
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


class Variable():
    __slots__ = ["name", "index", "ismono"]

    def __init__(self, name, index, ismono):
        self.name = name
        self.index = index
        self.ismono = ismono


class Length():
    __slots__ = ["variable"]

    def __init__(self, variable):
        self.variable = variable


"""class ArrayGen():
    __slots__ = ["generator", "name", "expr"]

    def __init__(self, generator, name=None, expr=None):
        self.generator = generator
        def gen(name, expr)"""



def display(node, indent=0):
    start = '  |' * indent + '->'
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

    elif isinstance(node, Length):
        print(start, "Length")
        display(node.variable, indent)
