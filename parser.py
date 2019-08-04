from fractions import Fraction
import sys

from rply import ParserGenerator

import AST
from lexer import lexer, all_tokens


pgen = ParserGenerator(
    all_tokens,
    precedence=[
        ('left', ['OR']),
        ('left', ['AND']),
        ('left', ['NOT']),
        ('left', ['LESS', 'LEQ', 'GREAT', 'GEQ', 'EQ', 'NEQ']),
        ('left', ['ADD', 'SUB']),
        ('left', ['MUL', 'DIV', 'IDIV', 'MOD']),
        ('left', ['POW'])
    ]
)


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


@pgen.production('expression : NOT expression')
@pgen.production('expression : SUB expression')
def expression_uniop(p):
    op, expr = p
    op_token = op.gettokentype()
    return AST.Uniop(op_token, expr)


# -------------------- variable -------------------- #

@pgen.production('variable : NAMELPAREN expression RPAREN')
def expression_parentheses(p):
    return p[1]



parser = pgen.build()

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        print(parser.parse(lexer.lex(f.read())))
