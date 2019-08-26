import sys

from rply import ParserGenerator, Token

import AST
import interpreting
from lexing import lexer, all_tokens


# -------------------------- Exceptions -------------------------- #

class RailwaySyntaxError(RuntimeError): pass
class RailwayIllegalMono(RailwaySyntaxError):  pass
class RailwaySelfmodification(RailwaySyntaxError):  pass
class RailwayModifyingYield(RailwaySyntaxError):  pass


# -------------- Conditions for searching the tree -------------- #

def search_mono_lookups(x):
    return isinstance(x, AST.Lookup) and x.ismono


def search_unyieldable(x):
    return not (isinstance(x, AST.Let)
                or isinstance(x, AST.Unlet)
                or isinstance(x, AST.Print))


def search_lookup_name(names):
    return lambda x: isinstance(x, AST.Lookup) and x.name in names


def collect_names(collection):
    def search_condition(x):
        if isinstance(x, AST.Lookup) or isinstance(x, AST.Parameter):
            collection.add(x.name)
        return False
    return search_condition


# This will need updating later (e.g. for push-pop and call-uncall)
def collect_lhs_names(collection):
    def search_condition(x):
        if isinstance(x, (AST.Modop,)):
            collection.add(x.lookup.name)
        return False
    return search_condition


# ------------------- main parser generation method ------------------- #

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
    @pgen.production('stmt : if')
    @pgen.production('stmt : loop')
    @pgen.production('stmt : modification')
    @pgen.production('stmt : do')
    @pgen.production('stmt : print')
    @pgen.production('statement : stmt NEWLINE')
    def statement(p):
        return p[0]

    # -------------------- do-yield-undo -------------------- #

    @pgen.production('do : DO NEWLINE'
                     '      statements'
                     '     YIELD NEWLINE'
                     '      statements UNDO')
    def do_yield_undo(p):
        do_lines = p[2]
        yield_lines = p[5]
        do_names = set()
        yield_mod_names = set()
        for line in do_lines:
            line.search(collect_names(do_names))
        for line in yield_lines:
            line.search(collect_lhs_names(yield_mod_names))
        both = do_names.intersection(yield_mod_names)
        if both:
            raise RailwayModifyingYield(
                f'YIELD block may not modify variable "{both.pop()}" '
                'which is used in the DO block')
        return tree.DoUndo(do_lines, yield_lines)

    # -------------------- print -------------------- #

    @pgen.production('print : PRINT expression')
    @pgen.production('print : PRINT string')
    def print_expression(p):
        return tree.Print(p[1])

    # -------------------- modification -------------------- #

    @pgen.production('modification : lookup MODADD expression')
    @pgen.production('modification : lookup MODSUB expression')
    @pgen.production('modification : lookup MODMUL expression')
    @pgen.production('modification : lookup MODDIV expression')
    def modification(p):
        lookup, op_token, expr = p
        op_name = op_token.gettokentype()
        op = tree.modops[op_name]
        inv_op = tree.inv_modops[op_name]
        if not lookup.ismono and expr.search(search_mono_lookups):
            raise RailwayIllegalMono(
                f'Modifying non-mono variable "{lookup.name}" '
                'using mono expression')
        if expr.search(search_lookup_name(set([lookup.name]))):
            raise RailwaySelfmodification(
                f'Statement uses "{lookup.name}" to modify itself')
        return tree.Modop(lookup, op, inv_op, expr, op_name)

    # -------------------- loop -------------------- #

    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN expression RPAREN')
    def loop(p):
        forward_condition = p[2]
        lines = p[5]
        backward_condition = p[8]
        return tree.Loop(forward_condition, lines, backward_condition)

    # -------------------- if -------------------- #

    @pgen.production('if : IF LPAREN expression RPAREN NEWLINE'
                     '     statements'
                     '     FI LPAREN expression RPAREN')
    @pgen.production('if : IF LPAREN expression RPAREN NEWLINE'
                     '     statements'
                     '     FI LPAREN RPAREN')
    @pgen.production('if : IF LPAREN expression RPAREN NEWLINE'
                     '     statements'
                     '     ELSE NEWLINE statements'
                     '     FI LPAREN expression RPAREN')
    @pgen.production('if : IF LPAREN expression RPAREN NEWLINE'
                     '     statements'
                     '     ELSE NEWLINE statements'
                     '     FI LPAREN RPAREN')
    def _if(p):
        _, _, enter_expr, _, _, lines = p[:6]
        p = p[6:]
        if p.pop(0).gettokentype() == 'ELSE':
            else_lines = p[1]
            p = p[4:]
        else:
            else_lines = []
            p.pop(0)  # LPAREN
        t = p.pop(0)  # expression or RPAREN
        exit_expr = enter_expr if isinstance(t, Token) else t
        return tree.If(enter_expr, lines, else_lines, exit_expr)

    # -------------------- let unlet -------------------- #

    # #@pgen.production('let : LET lookup EQ arraygen')
    @pgen.production('let : LET lookup')
    @pgen.production('let : LET lookup ASSIGN expression')
    def let(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        if not lookup.ismono and rhs.search(search_mono_lookups):
            raise RailwayIllegalMono(f'Initialising "{lookup.name}" '
                                     'using mono expression')
        return tree.Let(lookup, rhs)

    # @pgen.production('unlet : UNLET lookup EQ arraygen')
    @pgen.production('unlet : UNLET lookup')
    @pgen.production('unlet : UNLET lookup ASSIGN expression')
    def unlet(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        if not lookup.ismono and rhs.search(search_mono_lookups):
            raise RailwayIllegalMono(f'Unletting "{lookup.name}" '
                                     'using mono expression')
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
    @pgen.production('expression : expression MOD expression')
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
            return tree.Fraction(binop(lhs, rhs))
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
            return tree.Fraction(uniop(arg))
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
