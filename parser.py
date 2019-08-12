from fractions import Fraction
import sys

from rply import ParserGenerator

import AST
from lexer import lexer, all_tokens


pgen = ParserGenerator(
    all_tokens,
    precedence=[
        ('left', ['empty']),
        ('left', ['statements']),
        ('left', ['OR']),
        ('left', ['AND']),
        ('left', ['XOR']),
        ('left', ['LESS', 'LEQ', 'GREAT', 'GEQ', 'EQ', 'NEQ']),
        ('left', ['ADD', 'SUB']),
        ('left', ['MUL', 'DIV', 'IDIV', 'MOD']),
        ('left', ['POW']),
        ('right', ['NOT', 'NEG'])
    ]
)


# -------------------- func decl -------------------- #

@pgen.production('module : functions')
def module(p):
    return AST.Module(p[0])


@pgen.production('functions : func_decl')
@pgen.production('functions : func_decl functions')
def functions(p):
    if len(p) == 1:
        return [p[0]]
    return [p[0]] + p[1]


# -------------------- func decl -------------------- #

@pgen.production('func_decl : FUNC funcname LPAREN parameters RPAREN NEWLINE '
                 '            statements RETURN varname NEWLINE')
@pgen.production('func_decl : FUNC funcname LPAREN parameters RPAREN NEWLINE '
                 '            statements RETURN NEWLINE')
@pgen.production('func_decl : FUNC funcname LPAREN RPAREN NEWLINE '
                 '            statements RETURN varname NEWLINE')
@pgen.production('func_decl : FUNC funcname LPAREN RPAREN NEWLINE '
                 '            statements RETURN NEWLINE')
def func_decl(p):
    p.pop(0)  # FUNC
    name = p.pop(0)  # funcname
    isswitch = (name[0] == '~')
    p.pop(0)  # LPAREN
    params = p.pop(0)  # parameters or RPAREN
    if isinstance(params, list):
        p.pop(0)  # RPAREN
    else:
        params = []
    p.pop(0)  # NEWLINE
    lines = p.pop(0)
    p.pop(0)  # RETURN
    retname = p.pop(0) if len(p) == 2 else None
    return AST.Function(name=name,
                        isswitch=isswitch,
                        parameters=params,
                        lines=lines,
                        retname=retname)


@pgen.production('parameters : parameter')
@pgen.production('parameters : parameter COMMA parameters')
def parameters(p):
    if len(p) == 1:
        return [p[0]]
    return [p[0]] + p[2]


@pgen.production('parameter : varname')
@pgen.production('parameter : BORROWED varname')
def parameter(p):
    name = p.pop()
    ismono = (name[0] == '.')
    isborrowed = bool(p)
    return AST.Parameter(name, isborrowed, ismono)


# -------------------- statements -------------------- #

@pgen.production('statements : statement')
@pgen.production('statements : statement statements')
def statements(p):
    if not p:
        return []
    if len(p) == 1:
        return [p[0]]
    return [p[0]] + p[1]


@pgen.production('stmt : let')
@pgen.production('stmt : unlet')
@pgen.production('statement : stmt NEWLINE')
def statement(p):
    return p[0]


# -------------------- let unlet -------------------- #

# #@pgen.production('let : LET variable EQ arraygen')
@pgen.production('let : LET variable')
@pgen.production('let : LET variable ASSIGN expression')
def let(p):
    rhs = Fraction(0) if len(p) == 2 else p[3]
    variable = p[1]
    return AST.Let(variable, rhs)

# @pgen.production('unlet : UNLET variable EQ arraygen')
@pgen.production('unlet : UNLET variable')
@pgen.production('unlet : UNLET variable ASSIGN expression')
def unlet1(p):
    rhs = Fraction(0) if len(p) == 2 else p[3]
    variable = p[1]
    return AST.Unlet(variable, rhs)


# -------------------- expression -------------------- #

@pgen.production('expression : NUMBER')
def expression_number(p):
    return Fraction(p[0].getstr())


@pgen.production('expression : expression ADD expression')
@pgen.production('expression : expression SUB expression')
@pgen.production('expression : expression MUL expression')
@pgen.production('expression : expression DIV expression')
@pgen.production('expression : expression IDIV expression')
@pgen.production('expression : expression POW expression')
@pgen.production('expression : expression XOR expression')
@pgen.production('expression : expression OR expression')
@pgen.production('expression : expression AND expression')
@pgen.production('expression : expression LEQ expression')
@pgen.production('expression : expression GEQ expression')
@pgen.production('expression : expression NEQ expression')
@pgen.production('expression : expression EQ expression')
@pgen.production('expression : expression LESS expression')
@pgen.production('expression : expression GREAT expression')
def expression_binop(p):
    lhs, op, rhs = p
    op_token = op.gettokentype()
    return AST.Binop(lhs, op_token, rhs)


@pgen.production('expression : LPAREN expression RPAREN')
def expression_parentheses(p):
    return p[1]


@pgen.production('expression : variable')
@pgen.production('expression : LEN variable')
def expression_variable(p):
    variable = p.pop()
    if p:
        return AST.Length(variable)
    return variable


@pgen.production('expression : NOT expression')
@pgen.production('expression : SUB expression', precedence='NEG')
def expression_uniop(p):
    op, arg = p
    op_token = op.gettokentype()
    return AST.Uniop(op_token, arg)


# -------------------- variable -------------------- #

@pgen.production('variable : varname')
@pgen.production('variable : varname index')
def variable_name(p):
    name = p.pop(0)
    ismono = (name[0] == '.')
    index = p.pop() if p else tuple()
    return AST.Variable(name, index, ismono)


@pgen.production('index : LSQUARE expression RSQUARE')
@pgen.production('index : LSQUARE expression RSQUARE index')
def index_expression(p):
    if len(p) == 4:
        return (p[1],) + p[3]
    return (p[1],)


# -------------------- names -------------------- #

@pgen.production('varname : NAME')
@pgen.production('varname : MONO NAME')
@pgen.production('funcname : NAME')
@pgen.production('funcname : SWITCH NAME')
def index_expression(p):
    return ''.join(x.getstr() for x in p)


# -------------------- arraygen -------------------- #
"""
@pgen.production('arraygen : LSQUARE expression FOR NAME IN arraygen RSQUARE')
@pgen.production('arraygen : LSQUARE expression RSQUARE')
@pgen.production('arraygen : LSQUARE expression COMMA expression RSQUARE')
@pgen.production('arraygen : LSQUARE expression COMMA expression COMMA '
                 'expression RSQUARE')
def arraygen(p):
    if p[2].gettokentype() == 'for':
        pass"""

# -------------------- Build and Test -------------------- #

parser = pgen.build()

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        AST.display(parser.parse(lexer.lex(f.read())))
