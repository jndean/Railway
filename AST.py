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

    def __repr__(self):
        return str(self)


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

    def __repr__(self):
        return f'({self.lhs} {self.name} {self.rhs})'


class Uniop(ExpressionNode):
    __slots__ = ["op", "expr", "name"]

    def __init__(self, op, expr, name="UNNAMED", **kwargs):
        super().__init__(**kwargs)
        self.op = op
        self.expr = expr
        self.name = name

    def uses_var(self, name):
        return self.expr.uses_var(name)

    def __repr__(self):
        return f'{self.name}{self.expr}'


class Lookup(ExpressionNode):
    __slots__ = ["name", "index", "mononame"]

    def __init__(self, name, index, mononame, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.index = index
        self.mononame = mononame

    def uses_var(self, name):
        return (self.name == name) or any(i.uses_var(name) for i in self.index)

    def __repr__(self):
        if self.index:
            return f'{self.name}[{"][".join(repr(i) for i in self.index)}]'
        return self.name


class Parameter:
    __slots__ = ["name", "mononame", "isborrowed"]

    def __init__(self, name, mononame, isborrowed):
        self.name = name
        self.mononame = mononame
        self.isborrowed = isborrowed

    def __repr__(self):
        return repr(self.name)


class Length(ExpressionNode):
    __slots__ = ["lookup"]

    def __init__(self, lookup, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup

    def uses_var(self, name):
        return self.lookup.uses_var(name)

    def __repr__(self):
        return f'#{repr(self.lookup)}'


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


class ThreadID(ExpressionNode):
    __slots__ = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def uses_var(self, name):
        return False


class NumThreads(ExpressionNode):
    __slots__ = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def uses_var(self, name):
        return False


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
    __slots__ = ["lhs_lookup", "rhs_lookup", "lhs_idx", "rhs_idx"]

    def __init__(self, lhs_lookup, rhs_lookup, lhs_idx, rhs_idx, **kwargs):
        super().__init__(**kwargs)
        self.lhs_lookup = lhs_lookup
        self.rhs_lookup = rhs_lookup
        self.lhs_idx = lhs_idx
        self.rhs_idx = rhs_idx


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


class Barrier(StatementNode):
    __slots__ = ["name"]

    def __init__(self, name, **kwargs):
        super().__init__(**kwargs)
        super().__init__(**kwargs)
        self.name = name


class Mutex(StatementNode):
    __slots__ = ["name", "lines"]

    def __init__(self, name, lines, **kwargs):
        super().__init__(**kwargs)
        self.name = name
        self.lines = lines


class Try(StatementNode):
    __slots__ = ["lookup", "iterator", "lines"]

    def __init__(self, lookup, iterator, lines, **kwargs):
        super().__init__(**kwargs)
        self.lookup = lookup
        self.iterator = iterator
        self.lines = lines


class Catch(StatementNode):
    __slots__ = ["expression"]

    def __init__(self, expression, **kwargs):
        super().__init__(**kwargs)
        self.expression = expression


class Print(StatementNode):
    __slots__ = ["targets"]

    def __init__(self, targets, **kwargs):
        super().__init__(**kwargs)
        self.targets = targets


class PrintLn(StatementNode):
    __slots__ = ["targets"]

    def __init__(self, targets, **kwargs):
        super().__init__(**kwargs)
        self.targets = targets


class Global:
    __slots__ = ["lookup", "rhs"]

    def __init__(self, lookup, rhs):
        self.lookup = lookup
        self.rhs = rhs


class Import:
    __slots__ = ["filename", "alias"]

    def __init__(self, filename, alias):
        self.filename = filename
        self.alias = alias


class CallBlock:
    __slots__ = ["isuncall", "name", "num_threads", "borrowed_params"]

    def __init__(self, isuncall, name, num_threads, borrowed_params):
        self.isuncall = isuncall
        self.name = name
        self.num_threads = num_threads
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
