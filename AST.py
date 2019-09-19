from abc import ABC, abstractmethod
from fractions import Fraction as BuiltinFraction


binops = dict((k, None) for k in [
    'ADD', 'SUB', 'MUL', 'DIV', 'POW', 'IDIV', 'MOD', 'XOR',
    'OR', 'AND', 'LESS', 'LEQ', 'GREAT', 'GEQ', 'EQ', 'NEQ'])
uniops = dict((k, None) for k in [
    'NOT', 'SUB'])
modops = dict((k, None) for k in [
    'MODADD', 'MODSUB', 'MODMUL', 'MODDIV', 'MODIDIV', 'MODPOW', 'MODMOD',
    'MODXOR', 'MODOR', 'MODAND'])
inv_modops = dict((k, None) for k in [
    'MODADD', 'MODSUB', 'MODMUL', 'MODDIV'])


class ExpressionNode(ABC):
    __slots__ = ["hasmono"]

    def __init__(self, hasmono):
        self.hasmono = hasmono  # Node or subnode uses a mono variable

    @abstractmethod
    def uses_var(self, name):
        pass


class StatementNode(ABC):
    __slots__ = ["ismono", "modreverse"]

    def __init__(self, ismono, modreverse):
        self.ismono = ismono  # Node is only executed forward
        self.modreverse = modreverse  # (Sub)Node modifies a non-mono var


class Fraction(BuiltinFraction):
    hasmono = False

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


class Uniop(ExpressionNode):
    __slots__ = ["op", "expr", "name"]

    def __init__(self, op, expr, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.expr = expr
        self.name = name

    def uses_var(self, name):
        return self.expr.uses_var(name)


class Lookup(ExpressionNode):
    __slots__ = ["name", "index", "mononame"]

    def __init__(self, name, index, mononame, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.index = index
        self.mononame = mononame

    def uses_var(self, name):
        return (self.name == name) or any(i.uses_var(name) for i in self.index)


class Parameter:
    __slots__ = ["name", "mononame", "isborrowed"]

    def __init__(self, name, mononame, isborrowed):
        self.name = name
        self.mononame = mononame
        self.isborrowed = isborrowed


class Length(ExpressionNode):
    __slots__ = ["lookup"]

    def __init__(self, lookup, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup

    def uses_var(self, name):
        return self.lookup.uses_var(name)


class ArrayLiteral(ExpressionNode):
    __slots__ = ["items", "unowned"]

    def __init__(self, items, unowned, **kwargs):
        super().__init__(**kwargs)
        self.items = items
        self.unowned = unowned

    def uses_var(self, name):
        return any(x.uses_var(name) for x in self.items)


class ArrayRange(ExpressionNode):
    __slots__ = ["start", "stop", "step", "unowned"]

    def __init__(self, start, stop, step, unowned, **kwargs):
        super().__init__(**kwargs)
        self.start = start
        self.stop = stop
        self.step = step
        self.unowned = unowned

    def uses_var(self, name):
        return (self.start.uses_var(name)
                or self.step.uses_var(name)
                or self.stop.uses_var(name))


class ArrayTensor(ExpressionNode):
    __slots__ = ["fill_expr", "dims_expr", "unowned"]

    def __init__(self, fill_expr, dims_expr, unowned, **kwargs):
        super().__init__(**kwargs)
        self.fill_expr = fill_expr
        self.dims_expr = dims_expr
        self.unowned = unowned

    def uses_var(self, name):
        return (self.dims_expr.uses_var(name)
                or self.fill_expr.uses_var(name))


class Let(StatementNode):
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.rhs = rhs


class Unlet(StatementNode):
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs,  **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.rhs = rhs


class Promote(StatementNode):
    __slots__ = ["src_name", "dst_name"]

    def __init__(self, src_name, dst_name, **kwargs):
        super().__init__(**kwargs)
        self.src_name = src_name
        self.dst_name = dst_name


class Push(StatementNode):
    __slots__ = ["src_lookup", "dst_lookup"]

    def __init__(self, src_lookup, dst_lookup, **kwargs):
        super().__init__(**kwargs)
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup


class Pop(StatementNode):
    __slots__ = ["src_lookup", "dst_lookup"]

    def __init__(self, src_lookup, dst_lookup, **kwargs):
        super().__init__(**kwargs)
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup


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


class If(StatementNode):
    __slots__ = ["enter_expr", "lines", "else_lines", "exit_expr"]

    def __init__(self, enter_expr, lines, else_lines, exit_expr, **kwargs):
        super().__init__(**kwargs)
        self.enter_expr = enter_expr
        self.lines = lines
        self.else_lines = else_lines
        self.exit_expr = exit_expr


class Loop(StatementNode):
    __slots__ = ["forward_condition", "lines", "backward_condition"]

    def __init__(self, forward_condition, lines, backward_condition, **kwargs):
        super().__init__(**kwargs)
        self.forward_condition = forward_condition
        self.lines = lines
        self.backward_condition = backward_condition


class For(StatementNode):
    __slots__ = ["lookup", "iterator", "lines"]

    def __init__(self, lookup, iterator, lines, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.iterator = iterator
        self.lines = lines


class DoUndo(StatementNode):
    __slots__ = ["do_lines", "yield_lines"]

    def __init__(self, do_lines, yield_lines, **kwargs):
        super().__init__(**kwargs)
        self.do_lines = do_lines
        self.yield_lines = yield_lines


class Print(StatementNode):
    __slots__ = ["target"]

    def __init__(self, target, **kwargs):
        super().__init__(**kwargs)
        self.target = target


class CallBlock:
    __slots__ = ["isuncall", "name", "numthreads", "borrowed_params"]

    def __init__(self, isuncall, name, numthreads, borrowed_params):
        self.isuncall = isuncall
        self.name = name
        self.numthreads = numthreads
        self.borrowed_params = borrowed_params


class CallChain(StatementNode):
    __slots__ = ["in_params", "calls", "out_params"]

    def __init__(self, in_params, calls, out_params, **kwargs):
        super().__init__(**kwargs)
        self.in_params = in_params
        self.calls = calls
        self.out_params = out_params


class Function:
    __slots__ = ["name", "lines", "modreverse",
                 "borrowed_params", "borrowed_names",
                 "in_params", "in_names",
                 "out_params", "out_names"]

    def __init__(self, name, lines, modreverse, borrowed_params, in_params,
                 out_params):
        self.name = name
        self.lines = lines
        self.modreverse = modreverse
        self.borrowed_params = borrowed_params
        self.borrowed_names = set(p.name for p in borrowed_params)
        self.in_params = in_params
        self.in_names = set(p.name for p in in_params + borrowed_params)
        self.out_params = out_params
        self.out_names = set(p.name for p in out_params + borrowed_params)


class Module:
    __slots__ = ['functions', 'global_lines', 'name']

    def __init__(self, functions, global_lines, name='Unnamed'):
        self.functions = functions
        self.global_lines = global_lines
        self.name = name


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
