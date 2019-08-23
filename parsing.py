import sys

from rply import ParserGenerator

import AST
import interpreting
from lexing import lexer, all_tokens


# tree can be either the AST module or the interpreter module, creating
# a pure syntax tree or an interpreter tree (with eval methods) respectively
def generate_parser(tree):
    pgen = ParserGenerator(
        all_tokens,
        precedence=[
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
        funcs = dict((fun.name, fun) for fun in p[0])
        return tree.Module(funcs)

    @pgen.production('functions : func_decl')
    @pgen.production('functions : func_decl functions')
    def functions(p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[1]

    # -------------------- func decl -------------------- #

    @pgen.production('func_decl : FUNC funcname LPAREN parameters RPAREN'
                     '            NEWLINE statements RETURN varname NEWLINE')
    @pgen.production('func_decl : FUNC funcname LPAREN parameters RPAREN'
                     '            NEWLINE statements RETURN NEWLINE')
    @pgen.production('func_decl : FUNC funcname LPAREN RPAREN'
                     '            NEWLINE statements RETURN varname NEWLINE')
    @pgen.production('func_decl : FUNC funcname LPAREN RPAREN'
                     '            NEWLINE statements RETURN NEWLINE')
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
        return tree.Function(name=name,
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
        return tree.Parameter(name, isborrowed, ismono)

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
    @pgen.production('stmt : print')
    @pgen.production('statement : stmt NEWLINE')
    def statement(p):
        return p[0]

    # -------------------- print -------------------- #

    @pgen.production('print : PRINT expression')
    @pgen.production('print : PRINT string')
    def print_expression(p):
        return tree.Print(p[1])

    # -------------------- let unlet -------------------- #

    # #@pgen.production('let : LET lookup EQ arraygen')
    @pgen.production('let : LET lookup')
    @pgen.production('let : LET lookup ASSIGN expression')
    def let(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        return tree.Let(lookup, rhs)

    # @pgen.production('unlet : UNLET lookup EQ arraygen')
    @pgen.production('unlet : UNLET lookup')
    @pgen.production('unlet : UNLET lookup ASSIGN expression')
    def unlet(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        return tree.Unlet(lookup, rhs)

    # -------------------- expression -------------------- #

    @pgen.production('expression : NUMBER')
    def expression_number(p):
        return tree.Fraction(p[0].getstr())

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
        lhs, op_token, rhs = p
        name = op_token.gettokentype()
        binop = tree.binops[name]
        # Compile-time constant computation #
        if isinstance(lhs, tree.Fraction) and isinstance(rhs, tree.Fraction):
            return binop(lhs, rhs)
        return tree.Binop(lhs, binop, rhs, name)

    @pgen.production('expression : LPAREN expression RPAREN')
    def expression_parentheses(p):
        return p[1]

    @pgen.production('expression : lookup')
    @pgen.production('expression : LEN lookup')
    def expression_lookup(p):
        lookup = p.pop()
        if p:
            return tree.Length(lookup)
        return lookup

    @pgen.production('expression : NOT expression')
    @pgen.production('expression : SUB expression', precedence='NEG')
    def expression_uniop(p):
        op_token, arg = p
        name = op_token.gettokentype()
        uniop = tree.uniops[name]
        # Compile-time constant computation #
        if isinstance(arg, tree.Fraction):
            return uniop(arg)
        return tree.Uniop(uniop, arg, name)

    # -------------------- lookup -------------------- #

    @pgen.production('lookup : varname')
    @pgen.production('lookup : varname index')
    def lookup_varname(p):
        name = p.pop(0)
        ismono = (name[0] == '.')
        index = p.pop() if p else tuple()
        return tree.Lookup(name, index, ismono)

    @pgen.production('index : LSQUARE expression RSQUARE')
    @pgen.production('index : LSQUARE expression RSQUARE index')
    def index_expression(p):
        if len(p) == 4:
            return (p[1],) + p[3]
        return p[1],

    # -------------------- names -------------------- #

    @pgen.production('varname : NAME')
    @pgen.production('varname : MONO NAME')
    @pgen.production('funcname : NAME')
    @pgen.production('funcname : SWITCH NAME')
    def varfuncname_name(p):
        return ''.join(x.getstr() for x in p)

    # -------------------- string -------------------- #

    @pgen.production('string : STRING')
    def string_string(p):
        return p[0].getstr()[1:-1]

    # -------------------- arraygen -------------------- #
    """
    @pgen.production('arraygen : LSQUARE expression FOR NAME IN arraygen
     RSQUARE')
    @pgen.production('arraygen : LSQUARE expression RSQUARE')
    @pgen.production('arraygen : LSQUARE expression COMMA expression RSQUARE')
    @pgen.production('arraygen : LSQUARE expression COMMA expression COMMA '
                     'expression RSQUARE')
    def arraygen(p):
        if p[2].gettokentype() == 'for':
            pass"""

    # -------------------- Build and Test -------------------- #

    return pgen.build()


if __name__ == "__main__":
    parser = generate_parser(tree=interpreting)
    with open(sys.argv[1], 'r') as f:
        AST.display(parser.parse(lexer.lex(f.read())))
