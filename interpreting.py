from copy import deepcopy

import AST


# -------------------- Exceptions ----------------------  #

class RailwayException(RuntimeError):
    def __init__(self, message, scope):
        self.message = message
        self.stack = []
        while scope is not None:
            self.stack.append(scope.name)
            scope = scope.parent


class RailwayLeakedInformation(RailwayException): pass
class RailwayUndefinedVariable(RailwayException): pass
class RailwayVariableExists(RailwayException): pass
class RailwayIndexError(RailwayException): pass
class RailwayTypeError(RailwayException): pass
class RailwayUndefinedFunction(RailwayException): pass
class RailwayFailedAssertion(RailwayException): pass
class RailwayDirectionChange(RailwayException): pass
class RailwayReferenceOwnership(RailwayException): pass
class RailwayZeroError(RailwayException): pass
class RailwayValueError(RailwayException): pass
class RailwayCallError(RailwayException): pass
class RailwayIllegalMono(RailwayException): pass
class RailwayExpectedMono(RailwayException): pass
class RailwayExhaustedTry(RailwayException): pass


# -------------------- Interpreter-Only Objects ---------------------- #

class Scope:
    __slots__ = ['parent', 'name', 'functions', 'locals', 'monos', 'globals']

    def __init__(self, parent, name, locals, monos, globals, functions):
        self.parent = parent
        self.name = name
        self.functions = functions
        self.locals = locals if locals is not None else {}
        self.monos = monos if monos is not None else {}
        self.globals = globals if globals is not None else {}

    def lookup(self, name, locals=True, globals=True, monos=True):
        if monos and name in self.monos:
            return self.monos[name]
        if locals and name in self.locals:
            return self.locals[name]
        if globals and name in self.globals:
            return self.globals[name]
        if globals:
            msg = f'Variable "{name}" is undefined'
        else:
            msg = f'Local variable "{name}" is undefined'
        raise RailwayUndefinedVariable(msg, scope=self)

    def assign(self, name, var):
        if var.ismono:
            self.monos[name] = var
        else:
            if name in self.locals:
                raise RailwayVariableExists(
                    f'Variable "{name}" already exists',
                    scope=self)
            self.locals[name] = var

    def remove(self, name):
        if name in self.monos:
            del self.monos[name]
        elif name in self.locals:
            del self.locals[name]
        else:
            raise RailwayUndefinedVariable(
                f'Local variable "{name}" does not exist',
                scope=self)

    def lookup_func(self, name):
        if name not in self.functions:
            raise RailwayUndefinedFunction(f'Function "{name}" does not exist',
                                           scope=self)
        return self.functions[name]


class Variable:
    __slots__ = ['memory', 'ismono', 'isborrowed', 'isarray']

    def __init__(self, memory, ismono=False, isborrowed=False, isarray=False):
        self.memory = memory
        self.ismono = ismono
        self.isborrowed = isborrowed
        self.isarray = isarray


# ------------------------- AST Objects --------------------------#

class Module(AST.Module):
    def eval(self):
        scope = Scope(parent=None, name='unnamed', functions={},
                      locals={}, monos={}, globals={})
        for line in self.global_lines:
            line.eval(scope=scope, backwards=False)
        return scope.locals

    def main(self, argv):
        argv = Variable(memory=argv, ismono=False,
                        isborrowed=False, isarray=True)
        globals_ = self.eval()
        scope = Scope(parent=None, name='main', functions=self.functions,
                      locals={}, monos={}, globals=globals_)
        scope.assign('argv', argv)
        main = self.functions.get('main', self.functions.get('.main', None))
        if main is None:
            raise RailwayUndefinedFunction(
                f'There is no main function in {self.name}', scope=None)
        main.eval(scope, backwards=False)


# ---------------- AST - Function bodies and calls ----------------#

class Function(AST.Function):
    def eval(self, scope, backwards):
        if backwards:
            lines, out_names = reversed(self.lines), self.in_names
            out_params = self.in_params
        else:
            lines, out_names = self.lines, self.out_names
            out_params = self.out_params
        for line in lines:
            line.eval(scope, backwards=backwards)
        leaks = set(scope.locals).difference(out_names)
        if leaks:
            raise RailwayLeakedInformation(
                f'Variable "{leaks.pop()}" is still in scope of '
                f'function "{self.name}" at the end of a (un)call', scope=scope)
        return [scope.lookup(x.name, globals=False) for x in out_params]


class CallChain(AST.CallChain):
    def eval(self, scope, backwards):
        if backwards and self.ismono:
            return backwards
        params = self.out_params if backwards else self.in_params
        variables = [scope.lookup(p.name, globals=False) for p in params]
        for var, p in zip(variables, params):
            if var.isborrowed:
                raise RailwayReferenceOwnership(
                    f'Variable "{p.name}" is a borrowed reference and so may '
                    f'not be stolen by function "{self.calls[0].name}"',
                    scope=scope)
            scope.remove(p.name)
        for call in reversed(self.calls) if backwards else self.calls:
            variables = _eval_call(call, backwards, variables, scope)
        params = self.in_params if backwards else self.out_params
        if len(params) != len(variables):
            raise RailwayLeakedInformation(
                f'Function "{call.name}" returned {len(variables)} variables '
                f'but the result is assigned to {len(params)} variables', scope)
        for var, param in zip(variables, params):
            _check_mono_match(
                var, param, call.isuncall ^ backwards, call.name, scope)
            scope.assign(param.name, var)
        return backwards


def _eval_call(call, backwards, variables, scope):
    function = scope.lookup_func(call.name)
    uncall = call.isuncall ^ backwards
    params = function.out_params if uncall else function.in_params
    subscope = Scope(parent=scope,
                     name=call.name,
                     functions=scope.functions,
                     locals={}, monos={}, globals=scope.globals)
    if len(variables) != len(params):
        raise RailwayCallError(
            f'{"Unc" if uncall else "C"}alling function "{call.name}" with '
            f'{len(variables)} stolen references when it expects '
            f'{len(params)}', scope=scope)
    else:
        for var, param in zip(variables, params):
            _check_mono_match(var, param, uncall, call.name, scope)
            subscope.assign(param.name, var)
    for call_param, func_param in zip(call.borrowed_params,
                                      function.borrowed_params):
        var = scope.lookup(call_param.name)
        _check_mono_match(var, func_param, uncall, call.name, scope)
        new_var = Variable(memory=var.memory, ismono=var.ismono,
                           isborrowed=True, isarray=var.isarray)
        subscope.assign(func_param.name, new_var)
    return function.eval(scope=subscope, backwards=uncall)


def _check_mono_match(variable, parameter, isuncall, fname, scope):
    if variable.ismono and not parameter.mononame:
        callstr = 'Uncalling' if isuncall else 'Calling'
        raise RailwayIllegalMono(
            f'{callstr} function "{fname}" using mono argument for non-mono'
            f' parameter "{parameter.name}"', scope=scope)
    if parameter.mononame and not variable.ismono:
        callstr = 'Uncalling' if isuncall else 'Calling'
        raise RailwayIllegalMono(
            f'{callstr} function "{fname}" using non-mono argument for '
            f'mono parameter "{parameter.name}"', scope=scope)


CallBlock = AST.CallBlock


# -------------------- Try-Catch --------------------#

class Try(AST.Try):
    def eval(self, scope, backwards):
        if backwards:
            backwards = _run_lines(self.lines, scope, backwards)
            scope.remove(self.lookup.name)
            return backwards
        if hasattr(self.iterator, 'lazy_eval'):
            memory = self.iterator.lazy_eval(scope, backwards)
        else:
            memory = self.iterator.eval(scope)
            if isinstance(memory, Fraction):
                raise RailwayTypeError('The iterator provided to Try must be an'
                                       f' array, recieved a number', scope)
        # lines = self.lines[::-1] if backwards else self.lines
        name = self.lookup.name
        i = 0
        while i < len(memory):
            value = memory[i]
            if isinstance(value, Fraction):
                var = Variable(memory=[value], ismono=False, isborrowed=False,
                               isarray=False)
            else:
                var = Variable(memory=value, ismono=False, isborrowed=False,
                               isarray=True)
            scope.assign(name, var)
            caught = _run_lines(self.lines, scope, backwards)
            if caught:
                scope.remove(name)
                i += 1
            else:
                return backwards
        raise RailwayExhaustedTry(f'No value of "{name}" was uncaught', scope)


class Catch(AST.Catch):
    def eval(self, scope, backwards):
        if backwards:
            return backwards
        result = bool(self.expression.eval(scope))
        if result:
            print("Caught")
        return result


def _run_lines(lines, scope, backwards):
    i = len(lines) - 1 if backwards else 0
    while 0 <= i < len(lines):
        new_backwards = lines[i].eval(scope, backwards)
        if (new_backwards != backwards) and scope.monos:
            name = scope.monos.popitem()[0]
            raise RailwayDirectionChange('Direction of time changes with mono '
                                         f'variable "{name}" in scope', scope)
        backwards = new_backwards
        i = i-1 if backwards else i+1
    return backwards


# -------------------- AST - Print --------------------#

class Print(AST.Print):
    def eval(self, scope, backwards=False):
        if backwards:
            pass#return
        if isinstance(self.target, str):
            print(self.target)
        else:
            memory = self.target.eval(scope)
            print(self.stringify(memory))
        return backwards

    def stringify(self, memory):
        # Temporary implementation
        if isinstance(memory, Fraction):
            return str(memory)
        return '[' + ', '.join(self.stringify(elt) for elt in memory) + ']'


# -------------------- AST - Do-Yield-Undo --------------------#

class DoUndo(AST.DoUndo):
    def eval(self, scope, backwards):
        for line in self.do_lines:
            line.eval(scope, backwards=False)
        if scope.monos and backwards:
            name = next(iter(scope.monos.keys()))
            raise RailwayDirectionChange(
                'Changing direction of time at the end of a do block '
                f'whilst mono-directional variable "{name}" is in scope',
                scope=scope)
        yield_lines = self.yield_lines
        for line in reversed(yield_lines) if backwards else yield_lines:
            line.eval(scope, backwards)
        if scope.monos and not backwards:
            name = next(iter(scope.monos.keys()))
            raise RailwayDirectionChange(
                'Changing direction of time using an undo block '
                f'whilst mono-directional variable "{name}" is in scope',
                scope=scope)
        for line in reversed(self.do_lines):
            line.eval(scope, backwards=True)
        return backwards


# -------------------- AST - For --------------------#

class For(AST.For):
    def eval(self, scope, backwards):
        if hasattr(self.iterator, 'lazy_eval'):
            memory = self.iterator.lazy_eval(scope, backwards)
        else:
            memory = self.iterator.eval(scope)
            if isinstance(memory, Fraction):
                raise RailwayTypeError('For loop must iterate over array, '
                                       f'recieved number {memory}', scope=scope)
        lines = self.lines[::-1] if backwards else self.lines
        name = self.lookup.name
        i = len(memory)-1 if backwards else 0
        while 0 <= i < len(memory):
            elt = memory[i]
            backup = elt
            if not isinstance(elt, Fraction):
                raise RailwayTypeError('Assigning an array to for-loop '
                                       f'variable "{name}"', scope=scope)
            var = Variable(memory=[elt], ismono=self.lookup.mononame,
                           isborrowed=True, isarray=False)
            scope.assign(name, var)
            for line in lines:
                line.eval(scope, backwards)
            if var.memory[0] != memory[i]:
                raise RailwayValueError(
                    f'For loop variable "{name}" has value {var.memory[0]} '
                    f'after an iteration, but the source array has '
                    f'corresponding value {memory[i]}', scope=scope)
            scope.remove(name)
            i += -1 if backwards else 1

        return backwards


# -------------------- AST - Loop, If --------------------#

class Loop(AST.Loop):
    def eval(self, scope, backwards):
        if backwards and not self.modreverse:
            return True
        if backwards:
            condition = self.backward_condition
            assertion = self.forward_condition
        else:
            condition = self.forward_condition
            assertion = self.backward_condition
        if not self.ismono and assertion.eval(scope):
            raise RailwayFailedAssertion(
                'Loop reverse condition is true before loop start',
                scope=scope)
        while condition.eval(scope):
            backwards = _run_lines(self.lines, scope, backwards)
            if backwards:
                condition = self.backward_condition
                assertion = self.forward_condition
            else:
                condition = self.forward_condition
                assertion = self.backward_condition
            if (not self.ismono) and (not assertion.eval(scope)):
                raise RailwayFailedAssertion('Foward loop condition holds when'
                                             ' reverse condition does not',
                                             scope=scope)
        return backwards


class If(AST.If):
    def eval(self, scope, backwards):
        if backwards and not self.modreverse:
            return backwards
        enter_expr = self.exit_expr if backwards else self.enter_expr
        exit_expr = self.enter_expr if backwards else self.exit_expr
        enter_result = bool(enter_expr.eval(scope))
        lines = self.lines if enter_result else self.else_lines
        # lines = reversed(lines) if backwards else lines
        # new_backwards = _run_lines(lines, scope, backwards)
        for line in reversed(lines) if backwards else lines:
            line.eval(scope, backwards)
        if not self.ismono:
            exit_result = bool(exit_expr.eval(scope))
            if exit_result != enter_result:
                raise RailwayFailedAssertion(
                    'Failed exit assertion in if-fi statement',
                    scope=scope)
        return backwards


# -------------------- AST - Push Pop Swap --------------------#

class Push(AST.Push):
    def eval(self, scope, backwards):
        if backwards:
            if not self.ismono:
                pop_eval(scope, self.dst_lookup, self.src_lookup)
        else:
            push_eval(scope, self.src_lookup, self.dst_lookup)
        return backwards


def push_eval(scope, src_lookup, dst_lookup):
    dst_var = scope.lookup(dst_lookup.name)
    src_var = scope.lookup(src_lookup.name)
    dst_mem = dst_lookup.eval(scope)
    src_mem = src_lookup.eval(scope)
    if not dst_var.isarray:
        raise RailwayTypeError(f'PUSHing onto "{dst_lookup.name}" '
                               'which is a number, not an array',
                               scope=scope)
    if not isinstance(dst_mem, list):
        raise RailwayTypeError(
            f'Pushing onto a loction in "{dst_lookup.name}" which is '
            'a number, not an array',
            scope=scope)
    if src_var.isborrowed:
        raise RailwayReferenceOwnership(
            f'Pushing borrowed reference "{src_lookup.name}"',
            scope=scope)
    dst_mem.append(src_mem)
    scope.remove(src_lookup.name)


class Pop(AST.Pop):
    def eval(self, scope, backwards):
        if backwards:
            if not self.ismono:
                push_eval(scope, self.dst_lookup, self.src_lookup)
        else:
            pop_eval(scope, self.src_lookup, self.dst_lookup)
        return backwards


def pop_eval(scope, src_lookup, dst_lookup):
    # Opporunity for optimisation: the var.eval duplicates the scope.lookup
    src_var = scope.lookup(src_lookup.name)
    src_mem = src_lookup.eval(scope)
    if not src_var.isarray:
        raise RailwayTypeError(
            f'Trying to pop from "{src_lookup.name}" which is a '
            'number, not an array',
            scope=scope)
    try:
        contents = src_mem.pop()
    except IndexError:
        raise RailwayIndexError(
            f'Popping from empty array "{src_lookup.name}" (or an '
            'element therin)',
            scope=scope)
    isarray = isinstance(contents, list)
    var = Variable(memory=contents if isarray else [contents],
                   ismono=dst_lookup.mononame,
                   isarray=isarray)
    scope.assign(name=dst_lookup.name, var=var)


# ----------------------- AST - Promote -----------------------#

class Promote(AST.Promote):
    def eval(self, scope, backwards):
        if backwards:
            if scope.lookup(self.dst_name).isborrowed:
                raise RailwayReferenceOwnership(
                    'Unpromoting a borrowed reference to '
                    f'"{self.dst_name}"', scope=scope)
            scope.remove(self.dst_name)
        else:
            var = scope.lookup(self.src_name, globals=False)
            if var.isborrowed:
                raise RailwayReferenceOwnership('Promoting borrowed reference '
                                                f'to "{self.src_name}"', scope)
            scope.remove(self.src_name)
            var.ismono = False
            scope.assign(self.dst_name, var)
        return backwards


# -------------------- AST - Modifications --------------------#

class Modop(AST.Modop):
    def eval(self, scope, backwards):
        if backwards and self.ismono:
            return backwards
        op = self.inv_op if backwards else self.op
        lhs, rhs = self.lookup.eval(scope), self.expr.eval(scope)
        try:
            result = Fraction(op(lhs, rhs))
        except ZeroDivisionError:
            raise RailwayZeroError(
                ('Multiplying' if self.name == 'MODMUL' else 'Dividing') +
                f' variable "{self.lookup.name}" by 0', scope=scope)
        self.lookup.set(scope, result)
        # The seperate lookup.eval and lookup.set calls are
        # an opportunity for optimisation
        return backwards


# -------------------- AST - Let and Unlet --------------------#

class Let(AST.Let):
    def eval(self, scope, backwards):
        if backwards:
            if not self.ismono:
                unlet_eval(self, scope)
        else:
            let_eval(self, scope)
        return backwards


class Unlet(AST.Unlet):
    def eval(self, scope, backwards):
        if backwards:
            if not self.ismono:
                let_eval(self, scope)
        else:
            unlet_eval(self, scope)
        return backwards


def let_eval(self, scope):
    lhs, rhs = self.lookup, self.rhs
    value = rhs.eval(scope=scope)
    isarray = isinstance(value, list)
    if isinstance(value, Fraction):
        memory = [value]
    elif hasattr(rhs, 'unowned') and rhs.unowned:
        memory = value
    else:
        memory = deepcopy(value)
    var = Variable(memory=memory, ismono=lhs.mononame, isarray=isarray)
    scope.assign(name=lhs.name, var=var)


def unlet_eval(self, scope):
    lhs, rhs = self.lookup, self.rhs
    var = scope.lookup(name=lhs.name, globals=False)
    if var.isborrowed:
        raise RailwayReferenceOwnership(
            f'Unletting borrowed reference "{lhs.name}"', scope=scope)
    if not self.ismono:
        value = rhs.eval(scope=scope)
        if var.isarray != isinstance(value, list):
            t = ["number", "array"]
            raise RailwayTypeError(f'Trying to unlet {t[var.isarray]} '
                                   f'"{lhs.name}" using {t[not var.isarray]}',
                                   scope=scope)
        memory = value if isinstance(value, list) else [value]
        if var.memory != memory:
            raise RailwayValueError(f'Variable "{lhs.name}" does not match '
                                    'RHS during uninitialisation', scope=scope)
    scope.remove(lhs.name)


# -------------------- Arrays -------------------- #

class ArrayLiteral(AST.ArrayLiteral):
    def eval(self, scope):
        return [item.eval(scope) for item in self.items]


class ArrayRange(AST.ArrayRange):
    def eval(self, scope):
        val = self.start.eval(scope=scope)
        step = self.step.eval(scope=scope)
        stop = self.stop.eval(scope=scope)
        if (isinstance(val, list) or isinstance(step, list) or
                isinstance(stop, list)):
            raise RailwayValueError('An argument to an array range was a list',
                                    scope=scope)
        if step == 0:
            raise RailwayValueError(
                f'Step value for array range must be non-zero', scope=scope)
        out = []
        if step > 0:
            while val < self.stop:
                out.append(Fraction(val))
                val += self.step
        else:
            while val > self.stop:
                out.append(Fraction(val))
                val += self.step
        return out

    def lazy_eval(self, scope, backwards):
        start = self.start.eval(scope=scope)
        step = self.step.eval(scope=scope)
        stop = self.stop.eval(scope=scope)
        if (isinstance(start, list) or isinstance(step, list) or
                isinstance(stop, list)):
            raise RailwayValueError('An argument to an array range was a list',
                                    scope=scope)
        if step == 0:
            raise RailwayValueError(
                f'Step value for array range must be non-zero', scope=scope)
        length = (stop - start) // step
        return _LazyRange(start, step, length)


class _LazyRange:
    def __init__(self, start, step, length):
        self.start = start
        self.step = step
        self.length = length

    def __getitem__(self, item):
        if item >= self.length:
            raise IndexError('Iternal index error in array range')
        return Fraction(self.start + self.step * item)

    def __len__(self):
        return self.length


class ArrayTensor(AST.ArrayTensor):
    def eval(self, scope):
        dims = self.dims_expr.eval(scope=scope)
        err_msg = None
        if isinstance(dims, Fraction):
            err_msg = 'Tensor dimensions should be an array, got a number'
        elif not all(isinstance(x, Fraction) for x in dims):
            err_msg = 'Tensor dimensions should be an array of numbers only'
        elif not dims:
            err_msg = 'Empty array given as tensor dimensions'
        else:
            dims = [int(d) for d in dims]
            if not all(dims[:-1]):
                err_msg = 'Only the final dimension of a tensor may be zero'
            elif any(x < 0 for x in dims):
                err_msg = 'Tensor dimensions must be non-negative'
        if err_msg:
            raise RailwayIndexError(err_msg, scope=scope)
        fill = self.fill_expr.eval(scope=scope)
        if isinstance(fill, Fraction):
            return self._tensor_of_fill(dims, fill)
        else:
            return self._tensor_copy_fill(dims, fill)

    def _tensor_of_fill(self, dims, fill, depth=0):
        if depth < len(dims) - 1:
            return [self._tensor_of_fill(dims, fill, depth+1)
                    for _ in range(dims[depth])]
        return [fill] * dims[-1]

    def _tensor_copy_fill(self, dims, fill, depth=0):
        if depth < len(dims) - 1:
            return [self._tensor_copy_fill(dims, fill, depth+1)
                    for _ in range(dims[depth])]
        return [deepcopy(fill) for _ in range(dims[-1])]


# -------------------- Expressions -------------------- #

class Binop(AST.Binop):
    def eval(self, scope):
        lhs = self.lhs.eval(scope=scope)
        rhs = self.rhs.eval(scope=scope)
        if isinstance(lhs, list) or isinstance(rhs, list):
            raise RailwayTypeError(
                f'Binary operation {self.name} does not accept arrays',
                scope=scope)
        return Fraction(self.op(lhs, rhs))

    def eval_and(self, scope):
        lhs = self.lhs.eval(scope=scope)
        if not lhs:
            return Fraction(0)
        return Fraction(bool(self.rhs.eval(scope=scope)))

    def eval_or(self, scope):
        lhs = self.lhs.eval(scope=scope)
        if lhs:
            return Fraction(1)
        return Fraction(bool(self.rhs.eval(scope=scope)))


class Uniop(AST.Uniop):
    def eval(self, scope):
        val = self.expr.eval(scope=scope)
        if isinstance(val, list):
            raise RailwayTypeError(
                f'Unary operation {self.name} does not accept arrays',
                scope=scope)
        return Fraction(self.op(val))


class Length(AST.Length):
    def eval(self, scope):
        var = scope.lookup(self.lookup.name)
        if not var.isarray:
            raise RailwayTypeError(f'Variable "{self.lookup.name}" '
                                   'has no length as it is not an array',
                                   scope=scope)
        return Fraction(len(var.memory))


class Lookup(AST.Lookup):
    def eval(self, scope):
        var = scope.lookup(self.name)
        if var.isarray:  # Arrays
            index = [int(idx.eval(scope=scope)) for idx in self.index]
            output = var.memory
            try:
                for idx in index:
                    output = output[idx]
            except IndexError:
                index_repr = f'{self.name}[{", ".join(str(i) for i in index)}]'
                if isinstance(output, Fraction):
                    msg = 'Indexing into number during lookup '
                else:
                    msg = 'Out of bounds error accessing '
                raise RailwayIndexError(msg + index_repr, scope=scope)
        else:  # Non-arrays (numbers)
            if self.index:
                raise RailwayIndexError(
                    f'Indexing into {self.name} which is a number',
                    scope=scope)
            output = var.memory[0]
        return output

    def set(self, scope, value):
        var = scope.lookup(self.name)
        memory = var.memory
        if var.isarray:
            indices = [int(idx.eval(scope=scope)) for idx in self.index]
            lookup_str = f'{self.name}[{",".join(str(i) for i in indices)}]'
            try:
                for idx in indices[:-1]:
                    memory = memory[idx]
                index = indices[-1]
                if not isinstance(memory[index], Fraction):
                    raise RailwayTypeError(
                        f'Trying to modify array "{lookup_str}" with a number',
                        scope=scope)
            except (IndexError, TypeError) as e:
                if isinstance(memory, Fraction) or isinstance(e, TypeError):
                    msg = 'Indexing into number during lookup '
                else:
                    msg = 'Out of bounds error accessing '
                raise RailwayIndexError(msg + lookup_str, scope=scope)
        else:  # Non-array (so a number (so a special array of length 1))
            if self.index:
                raise RailwayIndexError(
                    f'Indexing into {self.name} which is a number',
                    scope=scope)
            index = 0
        memory[index] = value


class Fraction(AST.Fraction):
    def eval(self, scope=None):
        return self


# Parameters are never eval'd to don't need extending
Parameter = AST.Parameter


def __modop_mul(a, b):
    if b == 0:
        raise ZeroDivisionError()
    return a * b


def __modop_div(a, b):
    if b == 0:
        raise ZeroDivisionError()
    return a / b


binops = {'ADD': lambda a, b: a + b,
          'SUB': lambda a, b: a - b,
          'MUL': lambda a, b: a * b,
          'DIV': lambda a, b: a / b,
          'POW': lambda a, b: a ** b,
          'IDIV': lambda a, b: a // b,
          'MOD': lambda a, b: a % b,
          'XOR': lambda a, b: bool(a) ^ bool(b),
          'OR': lambda a, b: bool(a) | bool(b),
          'AND': lambda a, b: bool(a) & bool(b),
          'LESS': lambda a, b: a < b,
          'LEQ': lambda a, b: a <= b,
          'GREAT': lambda a, b: a > b,
          'GEQ': lambda a, b: a >= b,
          'EQ': lambda a, b: a == b,
          'NEQ': lambda a, b: a != b}

uniops = {'NOT': lambda x: not bool(x),
          'SUB': lambda x: -x}

modops = {'MODADD': binops['ADD'],
          'MODSUB': binops['SUB'],
          'MODMUL': __modop_mul,
          'MODDIV': __modop_div,
          'MODIDIV': binops['IDIV'],
          'MODPOW': binops['POW'],
          'MODMOD': binops['MOD'],
          'MODXOR': binops['XOR'],
          'MODOR': binops['OR'],
          'MODAND': binops['AND']}

inv_modops = {'MODADD': modops['MODSUB'],
              'MODSUB': modops['MODADD'],
              'MODMUL': modops['MODDIV'],
              'MODDIV': modops['MODMUL']}
