#!/usr/bin/env python3.7

from collections import deque
from fractions import Fraction as Frac
import re
import sys
from tokenize import tokenize

# ------------------------------ Errors ------------------------------ #

class RailwayError(RuntimeError): pass
class ExistsError(RailwayError): pass
class ParsingError(RailwayError): pass
class LetError(RailwayError): pass
class UnletError(RailwayError): pass
class ModificationError(RailwayError): pass
class LoopAssertError(RailwayError): pass
class MemAccessError(RailwayError): pass
class ZeroMultiplicationError(RailwayError): pass
class ZeroDivisionError(RailwayError): pass
class InformationLeakError(RailwayError): pass

# ------------------------------ Operations ------------------------------ #

def BINOP_ADD(a, b):
    return a + b
def BINOP_SUB(a, b):
    return a - b
def BINOP_MUL(a, b):
    return a * b
def BINOP_DIV(a, b):
    return a / b
def BINOP_POW(a, b):
    return a ** b
def BINOP_IDIV(a, b):
    return a // b
def BINOP_MOD(a, b):
    return a % b
def BINOP_XOR(a, b):
    return Frac(bool(a) ^ bool(b))
def BINOP_OR(a, b):
    return Frac(bool(a) | bool(b))
def BINOP_AND(a, b):
    return Frac(bool(a) & bool(b))

def BINOP_LESS(a, b):
    return Frac(a < b)
def BINOP_LEQ(a, b):
    return Frac(a <= b)
def BINOP_GREAT(a, b):
    return Frac(a > b)
def BINOP_GEQ(a, b):
    return Frac(a >= b)
def BINOP_EQ(a, b):
    return Frac(a == b)
def BINOP_NEQ(a, b):
    return Frac(a != b)

def OP_NOT(a):
    return Frac(not a)
def OP_NEG(a):
    return -a
UNARY_OPS = (OP_NOT, OP_NEG)

MODOP_ADD = BINOP_ADD
MODOP_SUB = BINOP_SUB
MODOP_XOR = BINOP_XOR
def MODOP_MUL(a, b):
    if b == 0:
        raise ZeroMultiplcationError()
    return a * b
def MODOP_DIV(a, b):
    if b == 0:
        raise ZeroDivisionError()
    return a / b
MODOP_inverter = {
    MODOP_ADD: MODOP_SUB,
    MODOP_SUB: MODOP_ADD,
    MODOP_MUL: MODOP_DIV,
    MODOP_DIV: MODOP_MUL,
    MODOP_XOR: MODOP_XOR
}
token_to_MODOP = {
    '+=': MODOP_ADD,
    '-=': MODOP_SUB,
    '*=': MODOP_MUL,
    '/=': MODOP_DIV
}
BINOPS = [('**', BINOP_POW,   1),
          ('*',  BINOP_MUL,   2),
          ('/',  BINOP_DIV,   2),
          ('//', BINOP_IDIV,  2),
          ('%',  BINOP_MOD,   2),
          ('+',  BINOP_ADD,   3),
          ('-',  BINOP_SUB,   3),
          ('<',  BINOP_LESS,  4),
          ('<=', BINOP_LEQ,   4),
          ('>',  BINOP_GREAT, 4),
          ('>=', BINOP_GEQ,   4),
          ('=',  BINOP_EQ,    4),
          ('!=', BINOP_NEQ,   4),
          ('^',  BINOP_XOR,   5),
          ('|',  BINOP_OR,    5),
          ('&',  BINOP_AND,   5)]
token_to_BINOP = dict(x[:2] for x in BINOPS)
BINOP_order = dict(x[1:] for x in BINOPS)

# ------------------------------ Objects ------------------------------ #

class Variable:

    __slots__ = ['memory', 'length']
    def __init__(self, memory, length):
        self.memory = memory
        self.length = length

    def set(self, val, index=0):
        if index >= self.length:
            raise MemAccessError(f'Error setting element {index} '
                                   f'in array of size {self.length}')
        self.memory[index] = val
        
    def get(self, index=0):
        if index >= self.length:
            raise MemAccessError(f'Error accessing element {index} '
                                   f'in array of size {self.length}')
        return self.memory[index]

    def copy(self):
        return Variable(memory=self.memory.copy(), length=self.length)

        
class Function:
    __slots__ = ['name', 'parameters', 'lines', 'return_parameters', 'undoreturn']
    def __init__(self, name, parameters, lines, return_parameters, undoreturn):
        self.name = name
        self.parameters = parameters
        self.lines = lines
        self.return_parameters = return_parameters
        self.undoreturn = undoreturn


# ------------------------------ Statements ------------------------------ #    

class Modification:
    __slots__ = ['lval', 'op', 'unop', 'expr']
    def __init__(self, lval, op, expr):
        self.lval = lval
        self.op = op
        self.unop = MODOP_inverter[op]
        self.expr = expr

class Assignment:
    __slots__ = ['lval', 'expr']
    def __init__(self, lval, expr):
        self.lval = lval
        self.expr = expr

class Unassignment:
    __slots__ = ['lval', 'expr']
    def __init__(self, lval, expr):
        self.lval = lval
        self.expr = expr

class If:
    __slots__ = ['enter_expr', 'true_lines', 'false_lines', 'exit_expr']
    def __init__(self, enter_expr, true_lines, false_lines, exit_expr):
        self.enter_expr = enter_expr
        self.true_lines = true_lines
        self.false_lines = false_lines
        self.exit_expr = exit_expr

class Loop:
    __slots__ = ['start_expr', 'lines', 'stop_expr']
    def __init__(self, start_expr, lines, stop_expr):
        self.start_expr = start_expr
        self.lines = lines
        self.stop_expr = stop_expr

class Swap:
    __slots__ = ['lval', 'rval']
    def __init__(self, lval, rval):
        self.lval = lval
        self.rval = rval

class Call:
    __slots__ = ['lvals', 'func', 'arguments']
    def __init__(self, lvals, func, arguments):
        self.lvals = lvals
        self.func = func
        self.arguments = arguments

class Uncall:
    __slots__ = ['lvals', 'func', 'arguments']
    def __init__(self, lvals, func, arguments):
        self.lvals = lvals
        self.func = func
        self.arguments = arguments

class Print:
    __slots__ = ['arguments']
    def __init__(self, arguments):
        self.arguments = arguments


# ------------------------------ Parser ------------------------------ #

NUMBER_REGEX = re.compile('\d+(\/\d+)?')
accepted_tokens = set((
    1,  # name
    2,  # number
    53  # op
))


class Parser():
    
    def __init__(self):
        self.lines_buffer = []

    def _get_line(self):
        out_line = []
        while not out_line:
            while True:
                t = next(self.tokens)
                if t[0] == 4:  # Newline token
                    break
                if t[0] in accepted_tokens:
                    out_line.append(t[1])
        return out_line
    
    def get_line(self):
        try:
            return self.lines_buffer.pop()
        except IndexError:
            return self._get_line()

    def peek_kwd(self):
        if not self.lines_buffer:
            ln = self._get_line()
            self.lines_buffer.append(ln)
        return self.lines_buffer[0][0]
        
    def parse(self, line_generator):
        self.tokens = tokenize(lambda: line_generator.readline())
        functions = {}
        while True:
            try:
                kwd = self.peek_kwd()
            except StopIteration:
                break
            if kwd == 'func':
                n, f = self.parse_func()
                if n in functions:
                    raise ExistsError(f'func {n} already defined')
                functions[n] = f
            elif kwd == 'global':
                self.parse_global()
            elif kwd == 'include':
                self.parse_include()
        return functions
    
    def parse_func(self):
        ln = self.get_line()
        func_name = ln[1]
        func_params = ln[2:]
        func_lines = []
        while True:
            if self.peek_kwd() in ('return', 'undoreturn'):
                break
            func_lines.append(self.parse_function_line())
        ln = self.get_line()
        func_undoreturn = ln[0] == 'undoreturn'
        func_return_params = ln[1:]
        function = Function(name=func_name,
                            parameters=func_params,
                            lines=func_lines,
                            return_parameters=func_return_params,
                            undoreturn=func_undoreturn)
        return func_name, function
    
    def parse_function_line(self):
        kwd = self.peek_kwd()
        if kwd in ('let', 'unlet'):
            return self.parse_assignment()
        elif kwd == 'if':
            return self.parse_if()
        elif kwd == 'print':
            return self.parse_print()
        elif kwd in ('else', 'fi', 'return', 'undoreturn',
                     'yrt', 'catch', 'until', 'unwith', 'yield'):
            raise ParsingError(f'Reached unexpected {kwd}')
        else:
            return self.parse_modification()
        
    def parse_expr(self, expr):
        if len(expr) == 0:
            raise ParsingError('Encountered empty expression')
        expr_lvl1 = []
        unary_ops = []
        depth = 0
        expecting_binop = False
        current_block = expr_lvl1
        for token in expr:
            # Handle extracting unary operations
            if depth == 0:
                if expecting_binop:
                    if token not in token_to_BINOP:
                        raise ParsingError(
                            f'Expected binary operator, got {token}')
                    expecting_binop = False
                    unary_ops.append(None)
                elif token in ('-', '!'):
                    unary_ops.append(OP_NOT if token is '!' else OP_NEG)
                    continue
                else:
                    unary_ops.append(None)
                    expecting_binop = True
                    
            # Handle nesting
            if token == '(':
                if depth == 0:
                    current_block = []
                else:
                    current_block.append(token)
                depth += 1
            elif token == ')':
                depth -= 1
                if depth < 0:
                    raise ParsingError('Unmatched parenthesis')
                elif depth == 0:
                    expr_lvl1.append(current_block)
                    current_block = expr_lvl1
                else:
                    current_block.append(token)
            else:
                current_block.append(token)

        if (len(expr_lvl1) % 2) != 1 or len(expr_lvl1) != len(unary_ops):
            ParsingError('Malformed expression')

        # Turn tokens into objects
        binops = deque(token_to_BINOP[t] for t in expr_lvl1[1::2])
        subexprs = deque()
        for subexpr, unary_op in zip(expr_lvl1[::2], unary_ops[::2]):
            if isinstance(subexpr, list):
                # Sub-expression
                s = self.parse_expr(subexpr)
            elif NUMBER_REGEX.fullmatch(subexpr) is not None:
                # Literal
                s = Frac(subexpr)
            elif subexpr.replace('_', '').isalnum():
                # Variable
                s = subexpr
            else:
                raise ParsingError(f'Malformed subexpr {subexpr}')
            if unary_op is not None:
                s = (unary_op, s)
            subexprs.append(s)
        
        # Turn object list into object tree
        while len(binops) > 0:
            new_binops, new_subexprs = deque(), deque()
            current_subexpr = subexprs.popleft()
            current_binop = binops.popleft()
            
            while binops:
                next_binop = binops.popleft()
                if BINOP_order[current_binop] > BINOP_order[next_binop]:
                    new_subexprs.append(current_subexpr)
                    new_binops.append(current_binop)
                    current_subexpr = subexprs.popleft()
                else:
                    current_subexpr = (current_binop,
                                       current_subexpr,
                                       subexprs.popleft())
                current_binop = next_binop
            new_subexprs.append((current_binop,
                                     current_subexpr,
                                     subexprs.popleft()))
            binops = new_binops
            subexprs = new_subexprs
        return subexprs.pop()

        
    def parse_assignment(self):
        ln = self.get_line()
        Statement = Assignment if ln[0] == 'let' else Unassignment
        if ln[2] != '=':
            raise ParsingError(f"Expected '=' in (un/)assignment, got {ln[2]}")
        return Statement(lval=ln[1], expr=self.parse_expr(ln[3:]))
        
    def parse_modification(self):
        ln = self.get_line()
        lval, modop_name, expr_tokens = ln[0], ln[1], ln[2:]
        if modop_name not in token_to_MODOP:
            raise ParsingError(f'Unrecognised mod-op {modop_name}')
        modop = token_to_MODOP[modop_name]
        if lval in expr_tokens:
            raise ModificationError(
                f'{lval} appears on left and right of modification')
        return Modification(lval=ln[0],
                            op=modop,
                            expr=self.parse_expr(ln[2:]))

    def parse_if(self):
        ln = self.get_line()
        enter_expr = self.parse_expr(ln[1:])
        true_lines, false_lines = [], []
        lines = true_lines
        while True:
            kwd = self.peek_kwd()
            if kwd == 'fi':
                break
            elif kwd == 'else':
                lines = false_lines
                self.get_line()
                continue
            lines.append(self.parse_function_line())
        ln = self.get_line()
        exit_expr = self.parse_expr(ln[1:])
        return If(enter_expr=enter_expr,
                  true_lines=true_lines,
                  false_lines=false_lines,
                  exit_expr=exit_expr)
        
    def parse_print(self):
        ln = self.get_line()
        return Print(arguments=ln[1:])
            

# ------------------------------ Interpreter ------------------------------ #

class Scope():
    globals = {}
    functions = {}
    
    def __init__(self, locals=None):
        self.locals = locals if locals is not None else {}

    def eval_expr(self, expr):
        if isinstance(expr, Frac):  # Number literal
            return expr
        if isinstance(expr, str):  # Variable name
            return self.locals[expr].get()
        if isinstance(expr, tuple):  # Operation
            if len(expr) == 3:  # Binary Op
                op, exp1, exp2 = expr
                return op(self.eval_expr(exp1), self.eval_expr(exp2))
            else:  # Unary Op
                op, subexpr = expr
                return op(self.eval_expr(subexpr))

    def run_lines(self, lines, backwards=False):
        if backwards:
            lines = reversed(lines)
        for line in lines:
            method = getattr(self, f'run_{type(line).__name__}')
            method(line, backwards)
        
    def run_Modification(self, modification, backwards=False):
        lval = self.resolve_var(modification.lval)
        op = modification.unop if backwards else modification.op
        rval = self.eval_expr(modification.expr)
        lval.set(op(lval.get(), rval))
            
    def run_Assignment(self, assignment, backwards=False):
        if not backwards:
            lval = assignment.lval
            if lval in self.locals:
                raise LetError(f'Variable {lval} already exists')
            rval_memory = [self.eval_expr(assignment.expr)]
            self.locals[lval] = Variable(memory=rval_memory, length=1)
        else:
            lval = assignment.lval
            if lval not in self.locals:
                raise ExistsError(f'Variable {lval} does not exist')
            rval = self.eval_expr(assignment.expr)
            if self.locals[lval].get() != rval:
                raise UnletError(f'Variable {lval} has value '
                                 f'{self.locals[lval].get()}, not {rval}')
            del self.locals[lval]

    def run_Unassignment(self, unassignment, backwards=False):
        self.run_Assignment(unassignment, backwards=not backwards)

    def run_If(self, if_, backwards=False):
        expr = if_.exit_expr if backwards else if_.enter_expr
        result = self.eval_expr(expr)
        lines = if_.true_lines if result else if_.false_lines
        self.run_lines(lines, backwards)

    def run_Loop(self, loop, backwards=False):
        assertion = loop.stop_expr if backwards else loop.start_expr
        test = loop.start_expr if backwards else loop.stop_expr
        if not self.eval_expr(assertion):
            raise LoopAssertionError(
                f'{assertion} is not true before entering loop')
        while not self.eval_expr(test):
            self.run_lines(loop.lines, backwards)

    def run_Swap(self, swap, backwards=False):
        lval = self.resolve_var(swap.lval)
        rval = self.resolve_var(swap.rval)
        l, r = lval.get(), rval.get()
        lval.set(r), rval.set(l)
        
    def run_Call(self, call, backwards=False):
        func = call.func
        
        if backwards and func.undoreturn:
            for name in call.lvals:
                del self.locals[name]

        elif backwards:
            args = [self.resolve_var(k) for k in call.arguments]
            new_locals = dict(zip(func.parameters, args))
            args = [self.resolve_var(k) for k in call.lvals]
            new_locals.update(dict(zip(func.return_parameters, args)))
            subscope = Scope(locals=new_locals)
            subscope.run_lines(func.lines, backwards=True)
            return_vars = [subscope.resolve_var(var)
                           for var in func.parameters]
            if any((v not in func.parameters and
                    v not in func.return_parameters)
                   for v in subscope.locals):
                raise InformationLeakError(
                    f'Function {func.name} returned but {v} persists')
            for name in call.lvals:
                del self.locals[name]

        else:
            func = call.func
            args = [self.resolve_var(k) for k in call.arguments]
            new_locals = dict(zip(func.parameters, args))
            subscope = Scope(locals=new_locals)
            subscope.run_lines(func.lines)
            if func.undoreturn:
                return_vars = [subscope.resolve_var(var).copy()
                              for var in func.return_parameters]
                subscope.run_lines(func.lines, backwards=True)
            else:
                return_vars = [subscope.resolve_var(var)
                               for var in func.return_parameters]
                if any((v not in func.parameters and
                        v not in func.return_parameters)
                       for v in subscope.locals):
                    raise InformationLeakError(
                        f'Function {func.name} returned but {v} persists')
            self.locals.update(dict(zip(call.lvals, return_vars)))

    def run_Uncall(self, uncall, backwards=False):
        raise NotImplementedError()
    
    def run_Print(self, print_, backwards=False):
        vals = [str(self.resolve_var(arg).get())
                for arg in print_.arguments]
        print(*vals)

    def resolve_var(self, lval):
        if lval in self.locals:
            return self.locals[lval]
        if lval in Scope.globals:
            return Scope.globals[lval]
        raise ExistsError(f'Variable {lval} does not exist')
            
        
        

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print(f'USAGE: {sys.argv[0]} filename.r')
        sys.exit()
        
    with open(sys.argv[1], 'rb') as f:
        functions = Parser().parse(f)
    Scope.functions = functions
    interpreter = Scope()
    interpreter.locals = {'argc': None, 'argv': None}
    main_call = Call([], functions['main'], [])
    interpreter.run_Call(main_call)
    quit()
        
    S = Scope()
    ax_bad = Assignment(lval='x', expr=Frac(1, 3))
    ax = Assignment(lval='x', expr=Frac(1, 2))
    un_ax = Unassignment(lval='x', expr=Frac(1, 2))
    ay = Assignment(lval='y', expr=Frac(1, 3))
    e = (BINOP_SUB, (BINOP_EQ, 'x', 'x'), Frac(1, 3))
    s = Modification(lval='y', op=MODOP_ADD, expr=e)
    if_ = If((BINOP_NEQ, 'x', 'x'),
             [Modification('y', MODOP_ADD, Frac(10, 1))],
             [Modification('y', MODOP_ADD, Frac(20, 1))],
             (BINOP_NEQ, 'x', 'x'))

    lines = [Assignment('A', Frac(1)),
             Assignment('n', Frac(6)),
             Assignment('i', Frac(0)),
             Loop(
                 (BINOP_EQ, 'i', Frac(0)),
                 [
                     Modification('A', MODOP_MUL, Frac(1, 5)),
                     Modification('i', MODOP_ADD, Frac(1))
                 ],
                 (BINOP_EQ, 'i', (BINOP_DIV, 'n', Frac(2)))),
             Unassignment('n', Frac(6))]
    

    function = Function(
        name='myF',
        parameters=['x'],
        lines=[
            Assignment('y', (BINOP_ADD, 'x', Frac(2)))
            ],
        return_parameters=['y'],
        undoreturn=False)
    
    func_lines = [Assignment('X', Frac(10)),
                  Call(lvals=['Y'],
                       func=function,
                       arguments=['X']),
                  Unassignment('X', Frac(10))]
    
    S.run_lines([ax, ay, s, if_, un_ax])
    S.run_Assignment(Assignment(lval='z1', expr='y'))
    
    S.run_lines(lines)
    S.run_Assignment(Assignment(lval='z2', expr='A'))
    
    S.run_lines(lines, backwards=True)
    S.run_lines([ax, ay, s, if_, un_ax], backwards=True)

    S.run_Swap(Swap('z1', 'z2'))
    S.run_Swap(Swap('z1', 'z2'))

    S.run_lines(func_lines)
    S.run_lines(func_lines, backwards=True)

    for n, v in S.locals.items():
        print(n, v.get())
