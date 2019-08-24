from fractions import Fraction as BuiltinFraction


binops = dict((k, None) for k in [
    'ADD', 'SUB', 'MUL', 'DIV', 'POW', 'IDIV', 'MOD', 'XOR',
    'OR', 'AND', 'LESS', 'LEQ', 'GREAT', 'GEQ', 'EQ', 'NEQ'])
uniops = dict((k, None) for k in [
    'NOT', 'SUB'])


Fraction = BuiltinFraction


class Binop:
    __slots__ = ["lhs", "op", "rhs", "name"]

    def __init__(self, lhs, op, rhs, name="UNNAMED"):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.name = name


class Uniop:
    __slots__ = ["op", "expr", "name"]

    def __init__(self, op, expr, name="UNNAMED"):
        self.op = op
        self.expr = expr
        self.name = name


class Lookup:
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
    __slots__ = ["lookup"]

    def __init__(self, lookup):
        self.lookup = lookup


class Let:
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs):
        self.lookup = lookup
        self.rhs = rhs


class Unlet:
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs):
        self.lookup = lookup
        self.rhs = rhs


class If:
    __slots__ = ["enter_expr", "lines", "else_lines", "exit_expr"]

    def __init__(self, enter_expr, lines, else_lines, exit_expr):
        self.enter_expr = enter_expr
        self.lines = lines
        self.else_lines = else_lines
        self.exit_expr = exit_expr


class Print:
    __slots__ = ["target"]

    def __init__(self, target):
        self.target = target


class Function:
    __slots__ = ["name", "isswitch", "parameters", "lines", "retname"]

    def __init__(self, name, isswitch, parameters, lines, retname):
        self.name = name
        self.isswitch = isswitch
        self.parameters = parameters
        self.lines = lines
        self.retname = retname


class Module:
    __slots__ = ['functions', 'name']

    def __init__(self, functions, name='Unnamed'):
        self.functions = functions
        self.name = name


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

    if isinstance(node, BuiltinFraction):
        print(start, str(node))

    elif isinstance(node, Binop):
        print(start, node.name)
        display(node.lhs, indent)
        display(node.rhs, indent)

    elif isinstance(node, Uniop):
        print(start, node.name)
        display(node.expr, indent)

    elif isinstance(node, Lookup):
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
        display(node.lookup, indent)

    elif isinstance(node, Let) or isinstance(node, Unlet):
        print(start, type(node).__name__)
        display(node.lookup, indent)
        display(node.rhs, indent)

    elif isinstance(node, list):
        for elt in node:
            display(elt, indent-1)

    elif isinstance(node, dict):
        for elt in node.values():
            display(elt, indent-1)

    elif isinstance(node, Function):
        print(start, "func", node.name)
        display(node.parameters, indent+1)
        display(node.lines, indent+1)
        print(start, "return", node.retname)

    elif isinstance(node, Module):
        display(node.functions, indent)
