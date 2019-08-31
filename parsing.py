import sys

from rply import ParserGenerator, Token

import AST
import interpreting
from lexing import lexer


# -------------------------- Exceptions -------------------------- #

class RailwaySyntaxError(RuntimeError): pass
class RailwayIllegalMono(RailwaySyntaxError): pass
class RailwaySelfmodification(RailwaySyntaxError): pass
class RailwayNoninvertibleModification(RailwaySyntaxError): pass
class RailwayBadSwitchMark(RailwaySyntaxError): pass
class RailwayTypeError(RailwaySyntaxError): pass


# ------------------- main parser generation method ------------------- #

# tree can be either the AST module or the interpreter module, creating
# a pure syntax tree or an interpreter tree (with eval methods) respectively
def generate_parser(tree):
    pgen = ParserGenerator(
        [rule.name for rule in lexer.rules],
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
        hasswitch = any(i.hasswitch for i in lines)
        if hasswitch and (name[0] != '~'):
            raise RailwayBadSwitchMark(
                f'Function "{name}" should be named "~{name}" since it uses '
                'control structures which change the direction of time')
        if not hasswitch and (name[0] == '~'):
            raise RailwayBadSwitchMark(
                f'Function "{name}" should not have a tilde since it contains '
                'no control structures which change the direction of time')
        modreverse = any(i.modreverse for i in lines)
        return tree.Function(name=name,
                             hasswitch=hasswitch,
                             parameters=params,
                             lines=lines,
                             retname=retname,
                             modreverse=modreverse)

    @pgen.production('parameters : parameter')
    @pgen.production('parameters : parameter COMMA parameters')
    def parameters(p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[2]

    @pgen.production('parameter : varname')
    @pgen.production('parameter : BORROWED varname')
    def parameter(p):
        name = p[-1]
        ismono = (name[0] == '.')
        isborrowed = (len(p) == 2)
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
    @pgen.production('stmt : push')
    @pgen.production('stmt : pop')
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
        modreverse = any(i.modreverse for i in do_lines + yield_lines)
        return tree.DoUndo(do_lines, yield_lines, hasswitch=True,
                           ismono=False, modreverse=modreverse)

    # -------------------- print -------------------- #

    @pgen.production('print : PRINT expression')
    @pgen.production('print : PRINT string')
    def print_expression(p):
        target = p[1]
        ismono = (not isinstance(target, str)) and target.hasmono
        return tree.Print(
            target, ismono=ismono, modreverse=False, hasswitch=False)

    # -------------------- modification -------------------- #

    @pgen.production('modification : lookup MODADD expression')
    @pgen.production('modification : lookup MODSUB expression')
    @pgen.production('modification : lookup MODMUL expression')
    @pgen.production('modification : lookup MODDIV expression')
    @pgen.production('modification : lookup MODIDIV expression')
    @pgen.production('modification : lookup MODPOW expression')
    @pgen.production('modification : lookup MODMOD expression')
    @pgen.production('modification : lookup MODXOR expression')
    @pgen.production('modification : lookup MODOR expression')
    @pgen.production('modification : lookup MODAND expression')
    def modification(p):
        lookup, op_token, expr = p
        op_name = op_token.gettokentype()
        op = tree.modops[op_name]
        ismono = lookup.hasmono or expr.hasmono
        if (not ismono) and op_name not in tree.inv_modops:
            raise RailwayNoninvertibleModification(
                f'Performing non-invertible operation {op_name} on non-mono '
                f'variable "{lookup.name}')
        inv_op = None if ismono else tree.inv_modops[op_name]
        modreverse = not lookup.mononame
        if ismono and modreverse:
            raise RailwayIllegalMono(
                f'Modifying non-mono variable "{lookup.name}" '
                'using mono information')
        if any(i.uses_var(lookup.name) for i in lookup.index)\
                or expr.uses_var(lookup.name):
            raise RailwaySelfmodification(
                f'Statement uses "{lookup.name}" to modify itself')
        return tree.Modop(lookup, op, inv_op, expr, op_name, ismono=ismono,
                          modreverse=modreverse, hasswitch=False)

    # -------------------- loop -------------------- #

    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN expression RPAREN')
    def loop(p):
        forward_condition = p[2]
        lines = p[5]
        backward_condition = p[8]
        ismono = forward_condition.hasmono or backward_condition.hasmono
        modreverse = any(i.modreverse for i in lines)
        hasswitch = any(i.hasswitch for i in lines)
        if ismono and modreverse:
            raise RailwayIllegalMono('Loop condition uses mono information '
                                     'and the body modifies a non-mono var')
        return tree.Loop(
            forward_condition, lines, backward_condition, ismono=ismono,
            hasswitch=hasswitch, modreverse=modreverse)

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
        ismono = enter_expr.has_mono or exit_expr.hasmono
        modreverse = any(i.modreverse for i in lines + else_lines)
        hasswitch = any(i.hasswitch for i in lines + else_lines)
        if ismono and modreverse:
            raise RailwayIllegalMono(
                'Using mono information in a branch condition which affects a '
                'non-mono variable')
        return tree.If(
            enter_expr, lines, else_lines, exit_expr, ismono=ismono,
            modreverse=modreverse, hasswitch=hasswitch)

    # -------------------- push pop swap -------------------- #

    @pgen.production('push : PUSH lookup RARROW lookup')
    @pgen.production('push : PUSH lookup LEQ lookup')
    def push(p):
        _, lhs, arrow, rhs = p
        ismono = lhs.hasmono or rhs.hasmono
        modreverse = (not lhs.mononame) or (not rhs.mononame)
        dst, src = (lhs, rhs) if arrow.gettokentype() == 'LEQ' else (rhs, lhs)
        if ((not dst.mononame) and
                (src.uses_var(dst.name) or
                 any(i.uses_var(dst.name) for i in dst.index))):
            raise RailwaySelfmodification('Push statment modifies variable '
                                          f'"{dst.name}" using itself')
        if src.index:
            raise RailwayTypeError(f'Pushing an element of array "{src.name}" '
                                   'would cause aliasing')
        if (not dst.hasmono) and ismono:
            raise RailwayIllegalMono(
                f'Pushing onto non-mono "{dst.name}" using mono information')
        if (not src.hasmono) and ismono:
            raise RailwayIllegalMono(
                f'Pushing non-mono "{src.name}" using mono information')
        return tree.Push(src_lookup=src, dst_lookup=dst, ismono=ismono,
                         modreverse=modreverse, hasswitch=False)

    @pgen.production('pop : POP lookup RARROW lookup')
    @pgen.production('pop : POP lookup LEQ lookup')
    def pop(p):
        _, lhs, arrow, rhs = p
        ismono = lhs.hasmono or rhs.hasmono
        modreverse = (not lhs.mononame) or (not rhs.mononame)
        dst, src = (lhs, rhs) if arrow.gettokentype() == 'LEQ' else (rhs, lhs)
        if dst.index:
            raise RailwayTypeError(
                f'Pop destination "{dst.name}" should not have indices')
        if any(i.uses_var(src.name) for i in src.index):
            raise RailwaySelfmodification('Pop statment modifies variable '
                                          f'"{src.name}" using itself')
        if (not dst.mononame) and ismono:
            raise RailwayIllegalMono(
                f'Pop creates non-mono "{dst.name}" using mono information')
        if (not src.mononame) and ismono:
            raise RailwayIllegalMono(
                f'Pop modifies non-mono "{src.name}" using mono information')
        return tree.Push(src_lookup=src, dst_lookup=dst, ismono=ismono,
                         modreverse=modreverse, hasswitch=False)

    # -------------------- let unlet -------------------- #

    # #@pgen.production('let : LET lookup EQ arraygen')
    @pgen.production('let : LET lookup')
    @pgen.production('let : LET lookup ASSIGN expression')
    def let(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        ismono = lookup.hasmono or rhs.hasmono
        modreverse = not lookup.mononame
        if (not lookup.mononame) and ismono:
            raise RailwayIllegalMono(f'Letting non-mono "{lookup.name}" '
                                     'using mono information')
        return tree.Let(
            lookup, rhs, ismono=ismono, modreverse=modreverse, hasswitch=False)

    # @pgen.production('unlet : UNLET lookup EQ arraygen')
    @pgen.production('unlet : UNLET lookup')
    @pgen.production('unlet : UNLET lookup ASSIGN expression')
    def unlet(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        ismono = lookup.hasmono or rhs.hasmono
        modreverse = not lookup.mononame
        if (not lookup.mononame) and ismono:
            raise RailwayIllegalMono(f'Unletting "{lookup.name}" '
                                     'using mono information')
        return tree.Unlet(
            lookup, rhs, ismono=ismono, modreverse=modreverse, hasswitch=False)

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
        hasmono = lhs.hasmono or rhs.hasmono
        # Compile-time constant computation #
        if isinstance(lhs, tree.Fraction) and isinstance(rhs, tree.Fraction):
            return tree.Fraction(binop(lhs, rhs))
        return tree.Binop(lhs, binop, rhs, name, hasmono=hasmono)

    @pgen.production('expression : LPAREN expression RPAREN')
    def expression_parentheses(p):
        return p[1]

    @pgen.production('expression : lookup')
    @pgen.production('expression : LEN lookup')
    def expression_lookup(p):
        lookup = p.pop()
        if p:
            return tree.Length(lookup, hasmono=lookup.hasmono)
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
        return tree.Uniop(uniop, arg, name, hasmono=arg.hasmono)

    # -------------------- lookup -------------------- #

    @pgen.production('lookup : varname')
    @pgen.production('lookup : varname index')
    def lookup_varname(p):
        name = p.pop(0)
        index = p.pop() if p else tuple()
        mononame = (name[0] == '.')
        hasmono = mononame or any(idx.hasmono for idx in index)
        return tree.Lookup(name=name, index=index,
                           mononame=mononame, hasmono=hasmono)

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
