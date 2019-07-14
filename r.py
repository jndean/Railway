from fractions import Fraction as Frac
import sys

class r_ConflictingDeclaration(RuntimeError): pass
class r_LetError(RuntimeError): pass
class r_UnletError(RuntimeError): pass
class r_LoopAssertError(RuntimeError): pass

def BINOP_ADD(a, b):
    return a + b
def BINOP_SUB(a, b):
    return a - b
def BINOP_MUL(a, b):
    return a * b
def BINOP_DIV(a, b):
    return a / b
def BINOP_INTDIV(a, b):
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

MODOP_ADD = BINOP_ADD
MODOP_SUB = BINOP_SUB
MODOP_MUL = BINOP_MUL
MODOP_DIV = BINOP_DIV
MODOP_XOR = BINOP_XOR
MODOP_inverter = {
    MODOP_ADD: MODOP_SUB,
    MODOP_SUB: MODOP_ADD,
    MODOP_MUL: MODOP_DIV,
    MODOP_DIV: MODOP_MUL,
    MODOP_XOR: MODOP_XOR
}


KWD_LET = 'let'
KWD_DO = 'do'
KWD_UNLET = 'unlet'


# -------------------- Objects -------------------- #

class Var:
    __slots__ = ['val']
    def __init__(self, val):
        self.val = val

        
class Function:
    __slots__ = ['parameters', 'lines', 'return_expr']
    def __init__(self, parameters, lines, return_expr):
        self.parameters = parameters
        self.lines = lines
        self.return_expr = return_expr


# -------------------- Lines -------------------- #    

class Statement:
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
    __slots__ = ['in_expr', 'true_lines', 'false_lines', 'out_expr']
    def __init__(self, in_expr, true_lines, false_lines, out_expr):
        self.in_expr = in_expr
        self.true_lines = true_lines
        self.false_lines = false_lines
        self.out_expr = out_expr

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

class Func:
    __slots__ = ['lval', ]


class Parser():
    def __init__(self):
        self.lines_buffer = []

    def _get_line(self):
        ln = False  # []
        while not ln:
            ln = next(self.line_generator)
            ln = ln.replace('(', ' ( ').replace(')', ' ) ')
            ln = ln.replace('{', ' ').replace('}', ' ')
            ln = ln.strip().split()
        return ln
    
    def get_line(self):
        try:
            return self.lines_buffer.pop()
        except IndexError:
            return self._get_line()

    def peak_kwd(self):
        if not self.lines_buffer:
            ln = self._get_line()
            self.lines_buffer.append(ln)
        return ln[0]
    
    def parse(self, line_generator):
        self.line_generator = line_generator
        ast = []
        while True:
            try:
                kwd = self.peak_kwd()
                method = getattr(self, f'parse_{kwd}')
                ast.append(method())
            except StopIteration:
                break

        for ln in ast:
            print(ln)
    
    def parse_func(self):
        res = []
        while True:
            ln = self.get_line()
            res.append(ln)
            if ln[0] in ['cpreturn', 'return']:
                break
        return res
   
    def parse_cpfunc(self):
        res = []
        while True:
            ln = self.get_line()
            res.append(ln)
            if ln[0] in ['cpreturn', 'return']:
                break
        return res
    
    def parse_let(self):
        pass

        

class Interpreter():
    globals = {}
    functions = {}
    
    def __init__(self):
        self.locals = {}

    def eval_expr(self, expr):
        if isinstance(expr, Frac):  # Number literal
            return expr
        if isinstance(expr, str):  # Variable name
            return self.locals[expr].val
        if isinstance(expr, tuple):  # Binary operation
            op, exp1, exp2 = expr
            return op(self.eval_expr(exp1), self.eval_expr(exp2))

    def run_lines(self, lines, backwards=False):
        if backwards:
            lines = reversed(lines)
        for line in lines:
            method = getattr(self, f'run_{type(line).__name__}')
            method(line, backwards)
        
    def run_Statement(self, statement, backwards=False):
        lval = self.resolve_lval(statement.lval)
        op = statement.unop if backwards else statement.op
        rval = self.eval_expr(statement.expr)
        lval.val = op(lval.val, rval)
            
    def run_Assignment(self, assignment, backwards=False):
        if not backwards:
            lval = assignment.lval
            if lval in self.locals:
                raise r_LetError(f'Variable {lval} already exists')
            rval = self.eval_expr(assignment.expr)
            self.locals[lval] = Var(rval)
        else:
            lval = assignment.lval
            if lval not in self.locals:
                raise r_UnletError(f'Variable {lval} does not exist')
            rval = self.eval_expr(assignment.expr)
            if self.locals[lval].val != rval:
                raise r_UnletError(f'Variable {lval} has value {self.locals[lval].val}, not {rval}')
            del self.locals[lval]

    def run_Unassignment(self, unassignment, backwards=False):
        self.run_Assignment(unassignment, backwards=not backwards)

    def run_If(self, if_, backwards=False):
        expr = if_.out_expr if backwards else if_.in_expr
        result = self.eval_expr(expr)
        lines = if_.true_lines if result else if_.false_lines
        self.run_lines(lines, backwards)

    def run_Loop(self, loop, backwards=False):
        assertion = loop.stop_expr if backwards else loop.start_expr
        test = loop.start_expr if backwards else loop.stop_expr
        if not self.eval_expr(assertion):
            raise r_LoopAssertionError(f'{assertion} is not true before entering loop')
        while not self.eval_expr(test):
            self.run_lines(loop.lines, backwards)

    def run_Swap(self, swap, backwards=False):
        lval = self.resolve_lval(swap.lval)
        rval = self.resolve_lval(swap.rval)
        tmp = lval.val
        lval.val = rval.val
        rval.val = tmp
        
    def run_Function(self, function, backwards=False):
        if backwards:
            raise NotImplementedError()
        else:
            arg_vals = [self.run_expr(expr) for expr in function.arguments]
            new_locals = dict(zip(function.arg_names, arg_vals))
            I = Interpreter(locals=new_locals)
            I.run_lines(function.lines)
            
        

    def resolve_lval(self, lval):
        if lval in self.locals:
            return self.locals[lval]
        return Interpreter.globals[lval]
            
        
        

if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print(f'USAGE: {sys.argv[0]} filename.r')
        sys.exit()
        
    with open(sys.argv[1], 'r') as f:
        Parser().parse(f)

    I = Interpreter()
    ax_bad = Assignment(lval='x', expr=Frac(1, 3))
    ax = Assignment(lval='x', expr=Frac(1, 2))
    un_ax = Unassignment(lval='x', expr=Frac(1, 2))
    ay = Assignment(lval='y', expr=Frac(1, 3))
    e = (BINOP_SUB, (BINOP_EQ, 'x', 'x'), Frac(1, 3))
    s = Statement(lval='y', op=MODOP_ADD, expr=e)
    if_ = If((BINOP_NEQ, 'x', 'x'),
             [Statement('y', MODOP_ADD, Frac(10, 1))],
             [Statement('y', MODOP_ADD, Frac(20, 1))],
             (BINOP_NEQ, 'x', 'x'))

    lines = [Assignment('A', Frac(1)),
             Assignment('n', Frac(6)),
             Assignment('i', Frac(0)),
             Loop(
                 (BINOP_EQ, 'i', Frac(0)),
                 [
                     Statement('A', MODOP_MUL, Frac(1, 5)),
                     Statement('i', MODOP_ADD, Frac(1))
                 ],
                 (BINOP_EQ, 'i', (BINOP_DIV, 'n', Frac(2)))),
             Unassignment('n', Frac(6))]
    
    
    I.run_lines([ax, ay, s, if_, un_ax])
    I.run_Assignment(Assignment(lval='z1', expr='y'))
    
    I.run_lines(lines)
    I.run_Assignment(Assignment(lval='z2', expr='A'))
    
    I.run_lines(lines, backwards=True)
    I.run_lines([ax, ay, s, if_, un_ax], backwards=True)

    I.run_Swap(Swap('z1', 'z2'))
    I.run_Swap(Swap('z1', 'z2'))

    for n, v in I.locals.items():
        print(n, v.val)
