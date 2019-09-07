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
class RailwayTypeError(RailwaySyntaxError): pass
class RailwayCircularDefinition(RailwaySyntaxError): pass
class RailwayUnexpectedIndex(RailwaySyntaxError): pass


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

    @pgen.production('functions : function')
    @pgen.production('functions : function functions')
    def functions(p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[1]

    # -------------------- func decl -------------------- #

    @pgen.production('function : FUNC NAME parameters parameters NEWLINE'
                     '            statements RETURN parameters NEWLINE')
    def function(p):
        _, name_t, borrowed_params, in_params, _, lines, _, out_params, _ = p
        name = name_t.getstr()
        modreverse = any(ln.modreverse for ln in lines)
        return tree.Function(name, lines, modreverse, borrowed_params,
                             in_params, out_params)

    @pgen.production('parameter_elts : parameter')
    @pgen.production('parameter_elts : parameter COMMA parameter_elts')
    @pgen.production('parameters : LPAREN RPAREN')
    @pgen.production('parameters : LPAREN parameter_elts RPAREN')
    def parameters(p):
        if isinstance(p[0], Token):
            return [] if isinstance(p[1], Token) else p[1]
        return [p[0]] if isinstance(p[0], tree.Lookup) else [p[0]] + p[2]

    @pgen.production('parameter : lookup')
    def parameter(p):
        if p[0].index:
            raise RailwayUnexpectedIndex(f'Function parameter "{p[0].name}" '
                                         f'has indices')
        return p[0]

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
        return tree.DoUndo(do_lines, yield_lines,
                           ismono=False, modreverse=modreverse)

    # -------------------- print -------------------- #

    @pgen.production('print : PRINT expression')
    @pgen.production('print : PRINT string')
    def print_expression(p):
        target = p[1]
        ismono = (not isinstance(target, str)) and target.hasmono
        return tree.Print(
            target, ismono=ismono, modreverse=False)

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
                f'variable "{lookup.name}"')
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
                          modreverse=modreverse)

    # -------------------- loop -------------------- #

    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN expression RPAREN')
    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN RPAREN')
    def loop(p):
        forward_condition = p[2]
        lines = p[5]
        backward_condition = None if (len(p) == 9) else p[8]
        ismono = (forward_condition.hasmono or (backward_condition is not None
                                                and backward_condition.hasmono))
        if ismono == (backward_condition is not None):
            raise RailwaySyntaxError('A loop should have a reverse condition '
                                     'if and only if it is bi-directional')
        modreverse = any(i.modreverse for i in lines)
        if ismono and modreverse:
            raise RailwayIllegalMono('Loop condition uses mono information '
                                     'and the body modifies a non-mono var')
        return tree.Loop(forward_condition, lines, backward_condition,
                         ismono=ismono, modreverse=modreverse)

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
        _, _, enter_expr, _, _, lines, *p = p
        if p[0].gettokentype() == 'ELSE':
            _, _, else_lines, _, _, *p = p
        else:
            else_lines = []
            p = p[2:]
        exit_expr = enter_expr if isinstance(p[0], Token) else p[0]
        ismono = enter_expr.hasmono or exit_expr.hasmono
        if ismono and (exit_expr is not enter_expr):
            raise RailwaySyntaxError('Provided a reverse condition for a mono-'
                                     'directional if-statement')
        modreverse = any(i.modreverse for i in lines + else_lines)
        if ismono and modreverse:
            raise RailwayIllegalMono(
                'Using mono information in a branch condition which affects a '
                'non-mono variable')
        return tree.If(enter_expr, lines, else_lines, exit_expr,
                       ismono=ismono, modreverse=modreverse)

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
                         modreverse=modreverse)

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
        return tree.Pop(src_lookup=src, dst_lookup=dst, ismono=ismono,
                        modreverse=modreverse)

    # -------------------- let unlet -------------------- #

    @pgen.production('let : LET lookup')
    @pgen.production('let : LET lookup ASSIGN expression')
    def let(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        ismono = lookup.hasmono or rhs.hasmono
        modreverse = not lookup.mononame
        if lookup.index:
            raise RailwayUnexpectedIndex('Indices on LHS when initialising '
                                         f'"{lookup.name}"')
        if (not lookup.mononame) and ismono:
            raise RailwayIllegalMono(f'Letting non-mono "{lookup.name}" '
                                     'using mono information')
        if rhs.uses_var(lookup.name):
            raise RailwayCircularDefinition(f'Variable "{lookup.name}" is used '
                                            'during its own initialisation')
        return tree.Let(lookup, rhs, ismono=ismono, modreverse=modreverse)

    @pgen.production('unlet : UNLET lookup')
    @pgen.production('unlet : UNLET lookup ASSIGN expression')
    def unlet(p):
        rhs = tree.Fraction(0) if len(p) == 2 else p[3]
        lookup = p[1]
        ismono = lookup.hasmono or rhs.hasmono
        modreverse = not lookup.mononame
        if lookup.index:
            raise RailwayUnexpectedIndex('Indices on LHS when unletting '
                                         f'"{lookup.name}"')
        if (not lookup.mononame) and ismono:
            raise RailwayIllegalMono(f'Unletting "{lookup.name}" '
                                     'using mono information')
        if rhs.uses_var(lookup.name):
            raise RailwayCircularDefinition(f'Variable "{lookup.name}" is used '
                                            'during its own unlet')
        return tree.Unlet(
            lookup, rhs, ismono=ismono, modreverse=modreverse)

    # -------------------- Arrays -------------------- #

    @pgen.production('expression : arrayliteral')
    @pgen.production('expression : arrayrange')
    @pgen.production('expression : arraytensor')
    def expression_array(p):
        return p[0]

    @pgen.production('expression_list : expression')
    @pgen.production('expression_list : expression COMMA expression_list')
    def expression_list(p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[2]

    @pgen.production('arrayliteral : LSQUARE expression_list RSQUARE')
    def arrayliteral(p):
        items = p[1]
        hasmono = any(x.hasmono for x in items)
        unowned = all(isinstance(x, tree.Fraction) or
                      (hasattr(x, 'unowned') and x.unowned)
                      for x in items)
        return tree.ArrayLiteral(items, hasmono=hasmono, unowned=unowned)

    @pgen.production('arrayrange : LSQUARE expression TO expression RSQUARE')
    @pgen.production('arrayrange : LSQUARE expression TO expression BY'
                     '             expression RSQUARE')
    def arrayrange(p):
        if len(p) == 5:
            _, start, _, stop, _ = p
            step = tree.Fraction(1)
        else:
            _, start, _, stop, _, step, _ = p
        hasmono = start.hasmono or stop.hasmono or step.hasmono
        return tree.ArrayRange(start, stop, step, hasmono=hasmono, unowned=True)

    @pgen.production('arraytensor : LSQUARE expression '
                     '             TENSOR expression RSQUARE')
    def arraytensor(p):
        _, fill_expr, _, dims_expr, _ = p
        hasmono = fill_expr.hasmono or dims_expr.hasmono
        return tree.ArrayTensor(fill_expr, dims_expr,
                                hasmono=hasmono, unowned=True)

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

    # @pgen.production('expression : arrayliteral')
    # def expression_arrayliteral(p):
    #     return p[0]

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

    # -------------------- Build -------------------- #

    return pgen.build()


if __name__ == "__main__":
    parser = generate_parser(tree=interpreting)
    with open(sys.argv[1], 'r') as f:
        AST.display(parser.parse(lexer.lex(f.read())))
