from fractions import Fraction as BuiltinFraction

import interpreting as interpreter


class RailwaySyntaxError(RuntimeError): pass
class RailwayIllegalMono(RailwaySyntaxError): pass
class RailwayExpectedMono(RailwaySyntaxError): pass
class RailwaySelfmodification(RailwaySyntaxError): pass
class RailwayNoninvertibleModification(RailwaySyntaxError): pass
class RailwayTypeError(RailwaySyntaxError): pass
class RailwayCircularDefinition(RailwaySyntaxError): pass
class RailwayUnexpectedIndex(RailwaySyntaxError): pass
class RailwayDuplicateDefinition(RailwaySyntaxError): pass
class RailwayNameConflict(RailwaySyntaxError): pass


class Token:  # Delete me?
    __slots__ = ['type', 'string', 'line', 'col', 'first_set']

    def __init__(self, type, string, line, col):
        self.type = type
        self.string = string
        self.line = line
        self.col = col
        self.first_set = {string}

    def __repr__(self):
        return self.string


class Fraction(BuiltinFraction):
    def compile(self):
        return interpreter.Fraction(self)

    def __repr__(self):
        return str(self)


class ThreadID:
    __slots__ = []

    def __repr__(self):
        return 'TID'

    def compile(self):
        return interpreter.ThreadID(hasmono=False)


class NumThreads:
    __slots__ = []

    def __repr__(self):
        return '#TID'

    def compile(self):
        return interpreter.NumThreads(hasmono=False)


class Lookup:
    __slots__= ['name', 'index']

    def __init__(self, name, index):
        self.name = name
        self.index = index

    def __repr__(self):
        if self.index:
            return f'{self.name}[{"][".join(repr(i) for i in self.index)}]'
        return self.name

    def compile(self):
        index = tuple(idx.compile() for idx in self.index)
        mononame = (self.name[0] == '.')
        hasmono = mononame or any(idx.hasmono for idx in index)
        if any(idx.uses_var(self.name) for idx in index):
            raise RailwaySelfmodification(f'Using "{self.name}" to index itself')
        return interpreter.Lookup(name=self.name, index=index,
                                  mononame=mononame, hasmono=hasmono)


class Parameter:
    __slots__ = ['name']

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return repr(self.name)

    def compile(self):
        mononame = (self.name[0] == '.')
        return interpreter.Lookup(name=self.name, index=tuple(),
                                  mononame=mononame, hasmono=mononame)


class Length:
    __slots__ = ['lookup']

    def __init__(self, lookup):
        self.lookup = lookup

    def __repr__(self):
        return f'#{repr(self.lookup)}'

    def compile(self):
        lookup = self.lookup.compile()
        return interpreter.Length(lookup, hasmono=lookup.hasmono)


class Binop:
    __slots__ = ['lhs', 'op', 'rhs']

    def __init__(self, lhs, op, rhs):
        self.lhs = lhs
        self.op = op
        self.rhs = rhs

    def __repr__(self):
        return f'({self.lhs} {self.op} {self.rhs})'

    def compile(self):
        lhs, rhs = self.lhs.compile(), self.rhs.compile()
        name = self.op.type
        binop = interpreter._binops[name]
        hasmono = lhs.hasmono or rhs.hasmono
        # Compile-time constant computation #
        if (isinstance(lhs, interpreter.Fraction) and
                isinstance(rhs, interpreter.Fraction)):
            return interpreter.Fraction(binop(lhs, rhs))
        node = interpreter.Binop(lhs, binop, rhs, name, hasmono=hasmono)
        # Special eval methods for binops that can short-circuit
        if name == 'AND':
            node.eval = node.eval_and
        elif name == 'OR':
            node.eval = node.eval_or
        return node


class Uniop:
    __slots__ = ['op', 'expr']

    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

    def __repr__(self):
        return f'{self.op}{self.expr}'

    def compile(self):
        name = self.op.string
        expr = self.expr.compile()
        uniop = interpreter._uniops[self.op.type]
        # Compile-time constant computation #
        if isinstance(expr, interpreter.Fraction):
            return interpreter.Fraction(uniop(expr))
        return interpreter.Uniop(uniop, expr, name, hasmono=expr.hasmono)


class ArrayLiteral:
    __slots__ = ['items']

    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return repr(self.items)

    def compile(self):
        items = [i.compile() for i in self.items]
        hasmono = any(i.hasmono for i in items)
        unowned = all(isinstance(i, interpreter.Fraction) or
                      (hasattr(i, 'unowned') and i.unowned)
                      for i in items)
        return interpreter.ArrayLiteral(items, hasmono=hasmono, unowned=unowned)


class ArrayRange:
    __slots__ = ['start', 'stop', 'step']

    def __init__(self, start, stop, step=None):
        self.start = start
        self.stop = stop
        self.step = step

    def __repr__(self):
        by_str = '' if self.step is None else f' by {self.step}'
        return f'[{self.start} to {self.stop}{by_str}]'

    def compile(self):
        step = (interpreter.Fraction(1) if self.step is None
                else self.step.compile())
        start = self.start.compile()
        stop = self.stop.compile()
        hasmono = start.hasmono or stop.hasmono or step.hasmono
        return interpreter.ArrayRange(start, stop, step,
                                      hasmono=hasmono, unowned=True)


class ArrayTensor:
    __slots__ = ['fill_expr', 'dims_expr']

    def __init__(self, fill_expr, dims_expr):
        self.fill_expr = fill_expr
        self.dims_expr = dims_expr

    def __repr__(self):
        return f'[{self.fill_expr} tensor {self.dims_expr}]'

    def compile(self):
        fill_expr = self.fill_expr.compile()
        dims_expr = self.dims_expr.compile()
        hasmono = fill_expr.hasmono or dims_expr.hasmono
        return interpreter.ArrayTensor(fill_expr, dims_expr,
                                       hasmono=hasmono, unowned=True)


class Let:
    __slots__ = ['name', 'rhs']

    def __init__(self, name, rhs):
        self.name = name
        self.rhs = rhs

    def __repr__(self):
        assignment = f' = {self.rhs}' if self.rhs is not None else' '
        return f'let {self.name}{assignment}'

    def compile(self):
        rhs = (interpreter.Fraction(0) if self.rhs is None
               else self.rhs.compile())
        mononame = (self.name[0] == '.')
        modreverse = not mononame
        ismono = mononame or rhs.hasmono
        if ismono and not mononame:
            raise RailwayIllegalMono(f'Letting non-mono "{self.name}" '
                                     'using mono information')
        if rhs.uses_var(self.name):
            raise RailwayCircularDefinition(f'Variable "{self.name}" is used '
                                            'during its own initialisation')
        lhs = interpreter.Lookup(self.name, index=tuple(),
                                 hasmono=mononame, mononame=mononame)
        return interpreter.Let(lhs, rhs, ismono=ismono, modreverse=modreverse)


class Unlet:
    __slots__ = ['name', 'rhs']

    def __init__(self, name, rhs):
        self.name = name
        self.rhs = rhs

    def __repr__(self):
        assignment = f' = {self.rhs}' if self.rhs is not None else' '
        return f'unlet {self.name}{assignment}'

    def compile(self):
        rhs = (interpreter.Fraction(0) if self.rhs is None
               else self.rhs.compile())
        mononame = self.name[0] == '.'
        ismono = mononame or rhs.hasmono
        modreverse = not mononame
        if ismono and not mononame:
            raise RailwayIllegalMono(f'Unletting "{self.name}" '
                                     'using mono information')
        if rhs.uses_var(self.name):
            raise RailwayCircularDefinition(f'Variable "{self.name}" is used '
                                            'during its own unlet')
        lhs = interpreter.Lookup(self.name, index=tuple(),
                                 hasmono=mononame, mononame=mononame)
        return interpreter.Unlet(
            lhs, rhs, ismono=ismono, modreverse=modreverse)


class Promote:
    __slots__ = ['src_name', 'dst_name']

    def __init__(self, src_name, dst_name):
        self.src_name = src_name
        self.dst_name = dst_name

    def __repr__(self):
        return f'promote {self.src_name} => {self.dst_name}'

    def compile(self):
        if self.src_name[0] != '.':
            raise RailwayExpectedMono(
                f'Promoting non-mono variable "{self.src_name}"')
        if self.dst_name[0] == '.':
            raise RailwayIllegalMono(
                f'Promoting to mono variable "{self.dst_name}"')
        return interpreter.Promote(
            src_name=self.src_name, dst_name=self.dst_name,
            modreverse=True, ismono=False)


class Push:
    __slots__ = ['src_lookup', 'dst_lookup']

    def __init__(self, src_lookup, dst_lookup):
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup

    def __repr__(self):
        return f'push {self.src_lookup} => {self.dst_lookup}'

    def compile(self):
        src, dst = self.src_lookup.compile(), self.dst_lookup.compile()
        ismono = src.hasmono or dst.hasmono
        modreverse = (not src.mononame) or (not dst.mononame)
        if ((not dst.mononame) and
                (src.uses_var(dst.name) or
                 any(i.uses_var(dst.name) for i in dst.index))):
            raise RailwaySelfmodification('Push statment modifies variable '
                                          f'"{dst.name}" using itself')
        if src.index:
            raise RailwayTypeError(f'Pushing an element of array "{src.name}" '
                                   'would cause aliasing')
        if ((not src.mononame) and
                (any(i.uses_var(src.name) for i in dst.index))):
            raise RailwaySelfmodification(
                f'Push source variable "{src.name}" is used in the destination '
                f'{self.dst_lookup}')
        if (not dst.hasmono) and ismono:
            raise RailwayIllegalMono(
                f'Pushing onto non-mono "{dst.name}" using mono information')
        if (not src.hasmono) and ismono:
            raise RailwayIllegalMono(
                f'Pushing non-mono "{src.name}" using mono information')
        return interpreter.Push(src_lookup=src, dst_lookup=dst, ismono=ismono,
                                modreverse=modreverse)


class Pop:
    __slots__ = ['src_lookup', 'dst_lookup']

    def __init__(self, src_lookup, dst_lookup):
        self.src_lookup = src_lookup
        self.dst_lookup = dst_lookup

    def __repr__(self):
        return f'pop {self.src_lookup} => {self.dst_lookup}'

    def compile(self):
        src, dst = self.src_lookup.compile(), self.dst_lookup.compile()
        ismono = src.hasmono or dst.hasmono
        modreverse = (not src.mononame) or (not dst.mononame)
        if dst.index:
            raise RailwayTypeError(
                f'Pop destination "{dst}" should be a name (not have indices)')
        if any(i.uses_var(src.name) for i in src.index):
            raise RailwaySelfmodification('Pop statment modifies variable '
                                          f'"{src.name}" using itself')
        if (not dst.mononame) and ismono:
            raise RailwayIllegalMono(
                f'Pop creates non-mono "{dst.name}" using mono information')
        if (not src.mononame) and ismono:
            raise RailwayIllegalMono(
                f'Pop modifies non-mono "{src.name}" using mono information')
        return interpreter.Pop(src_lookup=src, dst_lookup=dst, ismono=ismono,
                               modreverse=modreverse)


class Swap:
    __slots__ = ['lhs', 'rhs']

    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __repr__(self):
        return f'swap {self.lhs} <=> {self.rhs}'

    def compile(self):
        lhs, rhs = self.lhs.compile(), self.rhs.compile()
        ismono = lhs.hasmono or rhs.hasmono
        modreverse = not (lhs.mononame and rhs.mononame)
        if ismono and modreverse:
            raise RailwayIllegalMono(f'Using mono information to swap non-mono '
                                     f'"{lhs} <=> {rhs}"')
        if (any(idx.uses_var(rhs.name) for idx in lhs.index) or
                any(idx.uses_var(lhs.name) for idx in rhs.index)):
            raise RailwaySelfmodification(
                'Swap uses information from one side as an index on the other '
                f'"{lhs} <=> {rhs}"')
        if lhs.index:
            *lhs_idx, lhs_tail = lhs.index
            lhs.index = lhs_idx
        else:
            lhs_tail = None
        if rhs.index:
            *rhs_idx, rhs_tail = rhs.index
            rhs.index = rhs_idx
        else:
            rhs_tail = None
        return interpreter.Swap(lhs_lookup=lhs, rhs_lookup=rhs,
                                lhs_idx=lhs_tail, rhs_idx=rhs_tail,
                                ismono=ismono, modreverse=modreverse)


class If:
    __slots__ = ['enter_expr', 'lines', 'else_lines', 'exit_expr']

    def __init__(self, enter_expr, lines, else_lines, exit_expr):
        self.enter_expr = enter_expr
        self.lines = lines
        self.else_lines = else_lines
        self.exit_expr = exit_expr

    def __repr__(self):
        lines = [f'if ({self.enter_expr})'] + [repr(l) for l in self.lines]
        if self.else_lines is not None:
            lines += ['else'] + [repr(l) for l in self.else_lines]
        lines.append(f'fi ({self.exit_expr})')
        return '\n'.join(lines)


class Loop:
    __slots__ = ['forward_condition', 'lines', 'backward_condition']

    def __init__(self, forward_condition, lines, backward_condition):
        self.forward_condition = forward_condition
        self.lines = lines
        self.backward_condition = backward_condition

    def __repr__(self):
        return '\n'.join([f'loop ({self.forward_condition})'] +
                         [repr(l) for l in self.lines] +
                         [f'pool ({self.backward_condition})'])


class For:
    __slots__ = ['lookup', 'iterator', 'lines']

    def __init__(self, lookup, iterator, lines):
        self.lookup = lookup
        self.iterator = iterator
        self.lines = lines

    def __repr__(self):
        return '\n'.join([f'for ({self.lookup} in {self.iterator})'] +
                         [repr(l) for l in self.lines] +
                         ['rof'])


class Modop:
    __slots__ = ['lookup', 'op', 'expr']

    def __init__(self, lookup, op, expr):
        self.lookup = lookup
        self.op = op
        self.expr = expr

    def __repr__(self):
        return f'{self.lookup} {self.op} {self.expr}'


class Barrier:
    __slots__ = ['name']

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'barrier {self.name}'


class Mutex:
    __slots__ = ['name', 'lines']

    def __init__(self, name, lines):
        self.name = name
        self.lines = lines

    def __repr__(self):
        return '\n'.join([f'mutex {self.name}'] +
                         [repr(l) for l in self.lines] +
                         ['xetum'])


class PrintLn:
    __slots__ = ['items']

    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return f'println({", ".join(repr(i) for i in self.items)})'


class Print:
    __slots__ = ['items']

    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return f'print({", ".join(repr(i) for i in self.items)})'


class DoUndo:
    __slots__ = ['do_lines', 'yield_lines']

    def __init__(self, do_lines, yield_lines):
        self.do_lines = do_lines
        self.yield_lines = yield_lines

    def __repr__(self):
        lines = ['do'] + [repr(l) for l in self.do_lines]
        if self.yield_lines:
            lines += ['yield'] + [repr(l) for l in self.yield_lines]
        lines.append('undo')
        return '\n'.join(lines)


class Try:
    __slots__ = ['name', 'iterator', 'lines']

    def __init__(self, name, iterator, lines):
        self.name = name
        self.iterator = iterator
        self.lines = lines

    def __repr__(self):
        return '\n'.join([f'try ({self.name} in {self.iterator})'] +
                         [repr(l) for l in self.lines] +
                         ['yrt'])


class Catch:
    __slots__ = ['expr']

    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        return f'catch ({self.expr})'


class CallBlock:
    __slots__ = ["call", "name", "num_threads", "borrowed_params"]

    def __init__(self, call, name, num_threads, borrowed_params):
        self.call = call
        self.name = name
        self.num_threads = num_threads
        self.borrowed_params = borrowed_params

    def __repr__(self):
        out = f'{self.call} {self.name}'
        if self.num_threads:
            out += '{' + repr(self.num_threads) + '}'
        out += f'({", ".join(repr(p) for p in self.borrowed_params)})'
        return out


class Call:
    __slots__ = ['in_params', 'calls', 'out_params']

    def __init__(self, in_params, calls, out_params):
        self.in_params = in_params
        self.calls = calls
        self.out_params = out_params

    def __repr__(self):
        out = ''
        if self.in_params:
            out += f'({", ".join(repr(l) for l in self.in_params)}) => '
        out += ' => '.join(repr(c) for c in self.calls)
        if self.out_params:
            out += f' => ({", ".join(repr(l) for l in self.out_params)})'
        return out


class Function:
    __slots__ = ['name', 'borrowed_params', 'in_params', 'lines', 'out_params']

    def __init__(self, name, borrowed_params, in_params, lines, out_params):
        self.name = name
        self.borrowed_params = borrowed_params
        self.in_params = in_params
        self.lines = lines
        self.out_params = out_params

    def __repr__(self):
        out = f'func {self.name}('
        out += ', '.join(repr(p) for p in self.borrowed_params) + ')('
        out += ', '.join(repr(p) for p in self.in_params) + ')\n'
        out += '\n'.join(repr(l) for l in self.lines) + '\n'
        out += 'return (' + ', '.join(repr(p) for p in self.out_params) + ')'
        return out


class Global:
    __slots__ = ['name', 'expression']

    def __init__(self, name, expression):
        self.name = name
        self.expression = expression

    def __repr__(self):
        out = f'global {self.name}'
        if self.expression is not None:
            out += f' = {self.expression}'
        return out


class Import:
    __slots__ = ['path', 'name']

    def __init__(self, path, name):
        self.name = name
        self.path = path

    def __repr__(self):
        out = f'import "{self.path}"'
        if self.name is not None:
            out += f' as {self.name}'
        return out


class Module:
    __slots__ = ['items']

    def __init__(self, items):
        self.items = items

    def __repr__(self):
        return '\n'.join(repr(i) for i in self.items)
