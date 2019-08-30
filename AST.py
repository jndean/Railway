from abc import ABC, abstractmethod
from fractions import Fraction as BuiltinFraction


binops = dict((k, None) for k in [
    'ADD', 'SUB', 'MUL', 'DIV', 'POW', 'IDIV', 'MOD', 'XOR',
    'OR', 'AND', 'LESS', 'LEQ', 'GREAT', 'GEQ', 'EQ', 'NEQ'])
uniops = dict((k, None) for k in [
    'NOT', 'SUB'])
modops = dict((k, None) for k in [
    'MODADD', 'MODSUB', 'MODMUL', 'MODDIV'])


class ExpressionNode(ABC):
    __slots__ = ["hasmono"]

    def __init__(self, hasmono):
        self.hasmono = hasmono  # Node or subnode uses a mono variable

    @abstractmethod
    def uses_var(self, name):
        pass


class StatementNode(ABC):
    __slots__ = ["ismono", "modreverse", "hasswitch"]

    def __init__(self, ismono, modreverse, hasswitch):
        self.ismono = ismono  # Node is only executed forward
        self.modreverse = modreverse  # (Sub)Node modifies a non-mono var
        self.hasswitch = hasswitch  # (Sub)Node switches direction of time


class Fraction(BuiltinFraction):
    hasmono = False

    def search(self, condition):
        return condition(self)

    def uses_var(self, name):
        return False


class Binop(ExpressionNode):
    __slots__ = ["lhs", "op", "rhs", "name"]

    def __init__(self, lhs, op, rhs, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.lhs = lhs
        self.op = op
        self.rhs = rhs
        self.name = name

    def uses_var(self, name):
        return self.lhs.uses_var(name) or self.rhs.uses_var(name)

    def search(self, condition):
        return (condition(self)
                or self.lhs.search(condition)
                or self.rhs.search(condition))


class Uniop(ExpressionNode):
    __slots__ = ["op", "expr", "name"]

    def __init__(self, op, expr, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.expr = expr
        self.name = name

    def uses_var(self, name):
        return self.expr.uses_var(name)

    def search(self, condition):
        return condition(self) or self.expr.search(condition)


class Lookup(ExpressionNode):
    __slots__ = ["name", "index", "mononame"]

    def __init__(self, name, index, mononame, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.index = index
        self.mononame = mononame

    def uses_var(self, name):
        return (self.name == name) or any(i.uses_var(name) for i in self.index)

    def search(self, condition):
        return (condition(self)
                or any(x.search(condition) for x in self.index))


class Parameter:
    __slots__ = ["name", "mononame", "isborrowed"]

    def __init__(self, name, mononame, isborrowed):
        self.name = name
        self.mononame = mononame
        self.isborrowed = isborrowed

    def search(self, condition):
        return condition(self)


class Length(ExpressionNode):
    __slots__ = ["lookup"]

    def __init__(self, lookup, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup

    def uses_var(self, name):
        return self.lookup.uses_var(name)

    def search(self, condition):
        return condition(self) or self.lookup.search(condition)


class Let(StatementNode):
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.rhs = rhs

    def search(self, condition):
        return (condition(self)
                or self.lookup.search(condition)
                or self.rhs.search(condition))


class Unlet(StatementNode):
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs,  **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.rhs = rhs

    def search(self, condition):
        return (condition(self)
                or self.lookup.search(condition)
                or self.rhs.search(condition))


class Push(StatementNode):
    __slots__ = ["src_lookup", "dst_lookup"]

    def __init__(self, src_lookup, dst_lookup, **kwargs):
        super().__init__(**kwargs)
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup

    def search(self, condition):
        return (condition(self)
                or condition(self.src_lookup)
                or condition(self.dst_lookup))


class Pop(StatementNode):
    __slots__ = ["src_lookup", "dst_lookup"]

    def __init__(self, src_lookup, dst_lookup, **kwargs):
        super().__init__(**kwargs)
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup

    def search(self, condition):
        return (condition(self)
                or condition(self.src_lookup)
                or condition(self.dst_lookup))


class Swap(StatementNode):
    __slots__ = ["src_lookup", "dst_lookup"]

    def __init__(self, src_lookup, dst_lookup, **kwargs):
        super().__init__(**kwargs)
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup


class Modop(StatementNode):
    __slots__ = ["lookup", "op", "inv_op", "expr", "name"]

    def __init__(self, lookup, op, inv_op, expr, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.op = op
        self.inv_op = inv_op
        self.expr = expr
        self.name = name

    def search(self, condition):
        return (condition(self)
                or self.lookup.search(condition)
                or self.expr.search(condition))


class If(StatementNode):
    __slots__ = ["enter_expr", "lines", "else_lines", "exit_expr"]

    def __init__(self, enter_expr, lines, else_lines, exit_expr, **kwargs):
        super().__init__(**kwargs)
        self.enter_expr = enter_expr
        self.lines = lines
        self.else_lines = else_lines
        self.exit_expr = exit_expr

    def search(self, condition):
        return (condition(self)
                or self.enter_expr.search(condition)
                or self.exit_expr.search(condition)
                or any(x.search(condition) for x in self.lines)
                or any(x.search(condition) for x in self.else_lines))


class Loop(StatementNode):
    __slots__ = ["forward_condition", "lines", "backward_condition"]

    def __init__(self, forward_condition, lines, backward_condition, **kwargs):
        super().__init__(**kwargs)
        self.forward_condition = forward_condition
        self.lines = lines
        self.backward_condition = backward_condition

    def search(self, condition):
        return (condition(self)
                or self.forward_condition.search(condition)
                or self.backward_condition.search(condition)
                or any(x.search(condition) for x in self.lines))


class DoUndo(StatementNode):
    __slots__ = ["do_lines", "yield_lines"]

    def __init__(self, do_lines, yield_lines, **kwargs):
        super().__init__(**kwargs)
        self.do_lines = do_lines
        self.yield_lines = yield_lines

    def search(self, condition):
        return (condition(self)
                or any(ln.search(condition) for ln in self.do_lines)
                or any(ln.search(condition) for ln in self.yield_lines))


class Print(StatementNode):
    __slots__ = ["target"]

    def __init__(self, target, **kwargs):
        super().__init__(**kwargs)
        self.target = target

    def search(self, condition):
        return condition(self)


class Function:
    __slots__ = ["name", "hasswitch", "parameters", "lines", "retname",
                 "modreverse"]

    def __init__(self, name, hasswitch, parameters, lines, retname, modreverse):
        self.name = name
        self.hasswitch = hasswitch
        self.parameters = parameters
        self.lines = lines
        self.retname = retname
        self.modreverse = modreverse

    def search(self, condition):
        return (condition(self)
                or any(x.search(condition) for x in self.parameters)
                or any(x.search(condition) for x in self.lines))


class Module:
    __slots__ = ['functions', 'name']

    def __init__(self, functions, name='Unnamed'):
        self.functions = functions
        self.name = name

    def search(self, condition):
        return (condition(self)
                or any(x.search(condition) for x in self.functions))


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
        print(start, node.name + '[]' * len(node.index))
        for idx in node.index:
            display(idx, indent)

    elif isinstance(node, Parameter):
        out = '@' if node.isborrowed else ''
        out += '.'if node.mononame else ''
        out += node.name
        print(start, out)

    elif isinstance(node, Length):
        print(start, "LENGTH")
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

    elif isinstance(node, Print):
        print(start, 'PRINT')
        display(node.target, indent)

    elif isinstance(node, If):
        print(start, 'IF')
        display(node.enter_expr, indent)
        print(start, 'THEN')
        display(node.lines, indent)
        if node.else_lines:
            print(start, 'ELSE')
            display(node.else_lines, indent)
        print(start, 'FI')
        display(node.exit_expr, indent)

    elif isinstance(node, Modop):
        print(start, node.name)
        display(node.lookup, indent)
        display(node.expr, indent)

    elif isinstance(node, Loop):
        print(start, 'LOOP')
        display(node.forward_condition, indent)
        print(start, 'LOOP_BODY')
        display(node.lines, indent)
        print(start, 'WHILE')
        display(node.backward_condition, indent)

    elif isinstance(node, DoUndo):
        print(start, 'DO')
        display(node.do_lines, indent)
        print(start, 'YIELD')
        display(node.yield_lines, indent)
        print(start, 'UNDO')

    elif isinstance(node, Function):
        print(start, "FUNC", node.name)
        display(node.parameters, indent+1)
        display(node.lines, indent+1)
        print(start, "RETURN", node.retname)

    elif isinstance(node, Module):
        display(node.functions, indent)

    else:
        print("UNRECOGNISED NODE TYPE:", type(node))
