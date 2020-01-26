from collections import namedtuple, Counter
from os.path import split as os_split
import sys

from rply import ParserGenerator, Token
from rply import ParsingError as RplyParsingError

import interpreting
import lexing
import newlexer


__all__ = ['generate_parsing_function', 'RailwaySyntaxError']

parsing_func_cache = []
ParserState = namedtuple('ParserState', ['filename', 'parser'])

# -------------------------- Exceptions -------------------------- #

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


# ------------------- main parser generation method ------------------- #

# tree can be either the AST module or the interpreter module, creating
# a pure syntax tree or an interpreter tree (with eval methods) respectively
def generate_parsing_function(tree):
    if parsing_func_cache:
        return parsing_func_cache[0]
    pgen = ParserGenerator(
        [rule.name for rule in lexing.lexer.rules],
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

    # -------------------- Module definitions -------------------- #

    @pgen.production('module : filelevelitems')
    @pgen.production('module : NEWLINE filelevelitems')
    def module(state, p):
        items = p[-1]
        extern_funcs = {}  # Temporary
        funcs, global_lines = {}, []
        for item in items:
            if isinstance(item, tree.Function):
                if item.name in extern_funcs or item.name in funcs:
                    raise RailwayDuplicateDefinition(
                        f'Function {item.name} has multiple definitions')
                funcs[item.name] = item
            else:
                global_lines.append(item)
        return tree.Module(funcs, global_lines)

    @pgen.production('filelevelitems : filelevelitem')
    @pgen.production('filelevelitems : filelevelitem filelevelitems')
    def functions_globals(state, p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[1]

    @pgen.production('filelevelitem : function')
    @pgen.production('filelevelitem : global')
    @pgen.production('filelevelitem : import')
    def file_level_item(state, p):
        return p[0]

    # -------------------- import -------------------- #

    @pgen.production('import : IMPORT string NEWLINE')
    @pgen.production('import : IMPORT string AS NEWLINE')
    @pgen.production('import : IMPORT string AS NAME NEWLINE')
    def _import(state, p):
        filename = p[1]
        if filename[-5:] != '.rail':
            filename += '.rail'
        if len(p) == 3:
            alias = os_split(filename)[-1][:-5]
        elif len(p) == 4:
            alias = ''
        else:
            alias = p[-2].getstr()
        return tree.Import(filename=filename, alias=alias)

    # -------------------- global declaration -------------------- #

    """
    @pgen.production('global : let NEWLINE')
    def _global(state, p):
        if p[0].lookup.mononame:
            raise RailwayIllegalMono(f'GLobal variable "{p[0].lookup.name}" is '
                                     'declared mono')
        return p[0]
    """

    @pgen.production('global : GLOBAL lookup NEWLINE')
    @pgen.production('global : GLOBAL lookup ASSIGN expression NEWLINE')
    def _global(state, p):
        rhs = tree.Fraction(0) if len(p) == 3 else p[-2]
        lookup = p[1]
        if lookup.index:
            raise RailwayUnexpectedIndex('Indices on LHS when declaring global '
                                         f'"{lookup.name}"')
        if rhs.uses_var(lookup.name):
            raise RailwayCircularDefinition(f'Variable "{lookup.name}" is used '
                                            'during its own initialisation')
        if lookup.mononame:
            raise RailwayIllegalMono(
                f'Global variable "{lookup.name}" cannot be mono')
        return tree.Global(lookup, rhs)

    # -------------------- function declaration -------------------- #

    @pgen.production('function : FUNC name parameters parameters NEWLINE'
                     '           statements RETURN parameters NEWLINE')
    def function(state, p):
        _, name, borrowed_params, in_params, _, lines, _, out_params, _ = p
        modreverse = any(ln.modreverse for ln in lines)
        if modreverse == (name[0] == '.'):
            if modreverse:
                raise RailwayIllegalMono(f'Function "{name}" is marked as mono'
                                         ' but modifies non-mono variables')
            else:
                raise RailwayExpectedMono(f'Function "{name}" modifies no non-'
                                          'mono variables, so should be marked'
                                          ' as mono')
        in_counts = Counter(p.name for p in borrowed_params + in_params)
        out_counts = Counter(p.name for p in out_params)
        if len(in_counts) != len(borrowed_params) + len(in_params):
            dup, count = in_counts.most_common(1)[0]
            raise RailwayNameConflict(f'Parameter "{dup}" appears {count} times'
                                      f' in the signature of function "{name}"')
        if len(out_counts) != len(out_params):
            dup, count = out_counts.most_common(1)[0]
            raise RailwayNameConflict(f'Parameter "{dup}" is returned {count} '
                                      f'times by function "{name}"')
        return tree.Function(name, lines, modreverse, borrowed_params,
                             in_params, out_params)

    @pgen.production('parameter_elts : parameter')
    @pgen.production('parameter_elts : parameter COMMA parameter_elts')
    @pgen.production('parameters : LPAREN RPAREN')
    @pgen.production('parameters : LPAREN parameter_elts RPAREN')
    def parameters(state, p):
        if isinstance(p[0], Token):
            return [] if isinstance(p[1], Token) else p[1]
        return [p[0]] if len(p) == 1 else [p[0]] + p[2]

    @pgen.production('parameter : lookup')
    def parameter(state, p):
        if p[0].index:
            raise RailwayUnexpectedIndex(f'Function parameter "{p[0].name}" '
                                         f'has indices')
        return p[0]

    # -------------------- function call/uncall -------------------- #

    @pgen.production('callblock : CALL name parameters')
    @pgen.production('callblock : UNCALL name parameters')
    @pgen.production('callblock : CALL name LBRACK RBRACK parameters')
    @pgen.production('callblock : UNCALL name LBRACK RBRACK parameters')
    @pgen.production('callblock : CALL name LBRACK expression RBRACK'
                     '            parameters')
    @pgen.production('callblock : UNCALL name LBRACK expression RBRACK'
                     '            parameters')
    def callblock(state, p):
        isuncall = (p[0].gettokentype() == 'UNCALL')
        name = p[1]
        borrowed_params = p[-1]
        num_threads = p[3] if len(p) == 6 else None
        param_counts = Counter(p.name for p in borrowed_params)
        if len(param_counts) != len(borrowed_params):
            dup, count = param_counts.most_common(1)[0]
            raise RailwayNameConflict(f'(Un)call to function "{name}" borrows '
                                      f'parameter "{dup}" {count} times')
        return tree.CallBlock(isuncall, name, num_threads, borrowed_params)

    @pgen.production('callchain_right : callblock')
    @pgen.production('callchain_right : callblock GREAT callchain_right')
    @pgen.production('callchain_left  : callblock')
    @pgen.production('callchain_left  : callblock LESS callchain_left')
    def callchain(state, p):
        # The returned list if always left to right,
        # regardless of chain direction
        if len(p) == 1:
            return [p[0]]
        elif p[1].gettokentype() == 'GREAT':
            return [p[0]] + p[2]
        else:
            return p[2] + [p[0]]

    # No params
    @pgen.production('call_stmt : callchain_right')
    # Params on the left
    @pgen.production('call_stmt : parameters RARROW callchain_right')
    @pgen.production('call_stmt : parameters LEQ callchain_left')
    # Params on the left and right
    @pgen.production('call_stmt : parameters RARROW callchain_right'
                     '            RARROW parameters')
    @pgen.production('call_stmt : parameters LEQ callchain_left'
                     '            LEQ parameters')
    # Params on the right
    @pgen.production('call_stmt : callchain_right RARROW parameters')
    @pgen.production('call_stmt : callchain_left LEQ parameters')
    def callfunc(state, p):
        if len(p) == 1:  # No params
            in_params, calls, out_params = [], p[0], []
        else:
            in_params, out_params = [], []
            if isinstance(p[2][0], tree.CallBlock):  # Params on the left
                calls = p[2]
                if p[1].gettokentype() == 'RARROW':
                    in_params = p[0]
                else:
                    out_params = p[0]
            else:
                calls = p[0]
            if isinstance(p[-3][0], tree.CallBlock):  # Params on the right
                if p[-2].gettokentype() == 'RARROW':
                    out_params = p[-1]
                else:
                    in_params = p[-1]
        modreverse = any(call.name[0] != '.' for call in calls)
        ismono = not modreverse
        return tree.CallChain(in_params, calls, out_params,
                              modreverse=modreverse, ismono=ismono)

    # -------------------- statements -------------------- #

    @pgen.production('statements : statement')
    @pgen.production('statements : statement statements')
    def statements(state, p):
        if not p:
            return []
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[1]

    @pgen.production('stmt : let')
    @pgen.production('stmt : unlet')
    @pgen.production('stmt : if')
    @pgen.production('stmt : loop')
    @pgen.production('stmt : for')
    @pgen.production('stmt : try')
    @pgen.production('stmt : catch')
    @pgen.production('stmt : modification')
    @pgen.production('stmt : push')
    @pgen.production('stmt : pop')
    @pgen.production('stmt : swap')
    @pgen.production('stmt : do')
    @pgen.production('stmt : call_stmt')
    @pgen.production('stmt : promote')
    @pgen.production('stmt : print')
    @pgen.production('stmt : println')
    @pgen.production('stmt : barrier')
    @pgen.production('stmt : mutex')
    @pgen.production('statement : stmt NEWLINE')
    def statement(state, p):
        return p[0]

    # -------------------- try / catch -------------------- #

    @pgen.production('catch : CATCH expression')
    def catch(state, p):
        return tree.Catch(p[1], modreverse=False, ismono=True)

    @pgen.production('try : TRY LPAREN parameter IN expression RPAREN NEWLINE'
                     '      statements YRT')
    def _try(state, p):
        lookup, iterator, lines = p[2], p[4], p[7]
        if lookup.mononame:
            raise RailwayIllegalMono(
                f'Try statement assigns to mono name "{lookup.name}"')
        if iterator.hasmono:
            raise RailwayIllegalMono(f'Try statement has mono-directional '
                                     f'information in its iterator')
        return tree.Try(lookup=lookup, iterator=iterator, lines=lines,
                        ismono=False, modreverse=True)

    # -------------------- do-yield-undo -------------------- #

    @pgen.production('do : DO NEWLINE statements YIELD NEWLINE statements UNDO')
    @pgen.production('do : DO NEWLINE statements UNDO')
    def do_yield_undo(state, p):
        do_lines = p[2]
        yield_lines = p[5] if len(p) == 7 else []
        modreverse = any(i.modreverse for i in do_lines + yield_lines)
        return tree.DoUndo(do_lines, yield_lines,
                           ismono=False, modreverse=modreverse)

    # -------------------- print -------------------- #

    @pgen.production('println : PRINTLN LPAREN printables RPAREN')
    @pgen.production('print : PRINT LPAREN printables RPAREN')
    def print_expression(state, p):
        targets = p[2]
        ismono = any((not isinstance(t, str)) and t.hasmono
                     for t in targets)
        Node = tree.Print if p[0].getstr() == 'print' else tree.PrintLn
        return Node(targets, ismono=ismono, modreverse=False)

    @pgen.production('printables : string')
    @pgen.production('printables : expression')
    @pgen.production('printables : string COMMA printables')
    @pgen.production('printables : expression COMMA printables')
    def printable(state, p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[2]

    # -------------------- barrier, mutex -------------------- #

    @pgen.production('barrier : BARRIER string')
    def barrier(state, p):
        return tree.Barrier(name=p[1], ismono=False, modreverse=False)

    @pgen.production('mutex : MUTEX string NEWLINE statements XETUM')
    def mutex(state, p):
        return tree.Mutex(name=p[1], lines=p[3], ismono=False, modreverse=True)

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
    def modification(state, p):
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

    # -------------------- for -------------------- #

    @pgen.production('for : FOR LPAREN parameter IN expression RPAREN NEWLINE'
                     '         statements ROF')
    def _for(state, p):
        lookup, iterator, lines = p[2], p[4], p[7]
        modreverse = any(ln.modreverse for ln in lines)
        if iterator.hasmono and not lookup.mononame:
            raise RailwayIllegalMono(
                f'For loop uses non-mono name "{lookup.name}" for elements in a'
                ' mono iterator')
        # Using a mono varname and non-mono iterator needn't be mono
        ismono = iterator.hasmono
        if ismono and modreverse:
            raise RailwayIllegalMono('For loop is mono-directional but modifies'
                                     ' non-mono variables')
        return tree.For(lookup=lookup, iterator=iterator, lines=lines,
                        ismono=ismono, modreverse=modreverse)

    # -------------------- loop -------------------- #

    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN expression RPAREN')
    @pgen.production('loop : LOOP LPAREN expression RPAREN NEWLINE'
                     '         statements'
                     '       POOL LPAREN RPAREN')
    def loop(state, p):
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
    def _if(state, p):
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
    def push(state, p):
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
    def pop(state, p):
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

    @pgen.production('swap : SWAP lookup LRARROW lookup')
    def swap(state, p):
        _, lhs, arrow, rhs = p
        ismono = lhs.hasmono or rhs.hasmono
        modreverse = not (lhs.mononame and rhs.mononame)
        if ismono and modreverse:
            raise RailwayIllegalMono(f'Using mono information to swap non-mono '
                                     f'"{lhs.name}[?] <=> {rhs.name}[?]"')
        if (any(idx.uses_var(rhs.name) for idx in lhs.index) or
           any(idx.uses_var(lhs.name) for idx in rhs.index)):
            raise RailwaySelfmodification(
               'Swap uses information from one side as an index on the other '
               f'"{lhs.name}[?] <=> {rhs.name}[?]"')
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
        return tree.Swap(lhs_lookup=lhs, rhs_lookup=rhs,
                         lhs_idx=lhs_tail, rhs_idx=rhs_tail,
                         ismono=ismono, modreverse=modreverse)

    # --------------------- promote --------------------- #

    @pgen.production('promote : PROMOTE lookup RARROW lookup')
    @pgen.production('promote : PROMOTE lookup LEQ lookup')
    def promote(state, p):
        if p[2].gettokentype() == 'RARROW':
            src, dst = p[1], p[3]
        else:
            src, dst = p[3], p[1]
        if not src.mononame:
            raise RailwayExpectedMono(
                f'Promoting non-mono variable "{src.name}"')
        if dst.mononame:
            raise RailwayIllegalMono(f'Promoting to mono variable "{dst.name}"')
        for lookup in (src, dst):
            if lookup.index:
                raise RailwayUnexpectedIndex(
                    f'Indexing into "{lookup.name}" in promote statement')
        return tree.Promote(src_name=src.name, dst_name=dst.name,
                            modreverse=True, ismono=False)

    # -------------------- let unlet -------------------- #

    @pgen.production('let : LET lookup')
    @pgen.production('let : LET lookup ASSIGN expression')
    def let(state, p):
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
    def unlet(state, p):
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
    def expression_array(state, p):
        return p[0]

    @pgen.production('expression_list : expression')
    @pgen.production('expression_list : expression COMMA expression_list')
    def expression_list(state, p):
        if len(p) == 1:
            return [p[0]]
        return [p[0]] + p[2]

    @pgen.production('arrayliteral : LSQUARE RSQUARE')
    @pgen.production('arrayliteral : LSQUARE expression_list RSQUARE')
    def arrayliteral(state, p):
        items = p[1] if len(p) == 3 else []
        hasmono = any(x.hasmono for x in items)
        unowned = all(isinstance(x, tree.Fraction) or
                      (hasattr(x, 'unowned') and x.unowned)
                      for x in items)
        return tree.ArrayLiteral(items, hasmono=hasmono, unowned=unowned)

    @pgen.production('arrayrange : LSQUARE expression TO expression RSQUARE')
    @pgen.production('arrayrange : LSQUARE expression TO expression BY'
                     '             expression RSQUARE')
    def arrayrange(state, p):
        if len(p) == 5:
            _, start, _, stop, _ = p
            step = tree.Fraction(1)
        else:
            _, start, _, stop, _, step, _ = p
        hasmono = start.hasmono or stop.hasmono or step.hasmono
        return tree.ArrayRange(start, stop, step, hasmono=hasmono, unowned=True)

    @pgen.production('arraytensor : LSQUARE expression '
                     '             TENSOR expression RSQUARE')
    def arraytensor(state, p):
        _, fill_expr, _, dims_expr, _ = p
        hasmono = fill_expr.hasmono or dims_expr.hasmono
        return tree.ArrayTensor(fill_expr, dims_expr,
                                hasmono=hasmono, unowned=True)

    # -------------------- expression -------------------- #

    @pgen.production('expression : NUMBER')
    def expression_number(state, p):
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
    def expression_binop(state, p):
        lhs, op_token, rhs = p
        name = op_token.gettokentype()
        binop = tree.binops[name]
        hasmono = lhs.hasmono or rhs.hasmono
        # Compile-time constant computation #
        if isinstance(lhs, tree.Fraction) and isinstance(rhs, tree.Fraction):
            return tree.Fraction(binop(lhs, rhs))
        node = tree.Binop(lhs, binop, rhs, name, hasmono=hasmono)
        return node

    @pgen.production('expression : LPAREN expression RPAREN')
    def expression_parentheses(state, p):
        return p[1]

    @pgen.production('expression : lookup')
    @pgen.production('expression : LEN lookup')
    def expression_lookup(state, p):
        lookup = p.pop()
        if p:
            return tree.Length(lookup, hasmono=lookup.hasmono)
        return lookup

    @pgen.production('expression : NOT expression')
    @pgen.production('expression : SUB expression', precedence='NEG')
    def expression_uniop(state, p):
        op_token, arg = p
        name = op_token.gettokentype()
        uniop = tree.uniops[name]
        # Compile-time constant computation #
        if isinstance(arg, tree.Fraction):
            return tree.Fraction(uniop(arg))
        return tree.Uniop(uniop, arg, name, hasmono=arg.hasmono)

    # -------------------- lookup -------------------- #

    @pgen.production('lookup : name')
    @pgen.production('lookup : name index')
    def lookup_varname(state, p):
        name = p.pop(0)
        index = p.pop() if p else tuple()
        mononame = (name[0] == '.')
        hasmono = mononame or any(idx.hasmono for idx in index)
        if any(idx.uses_var(name) for idx in index):
            raise RailwaySelfmodification(f'Using "{name}" to index itself')
        return tree.Lookup(name=name, index=index,
                           mononame=mononame, hasmono=hasmono)

    @pgen.production('index : LSQUARE expression RSQUARE')
    @pgen.production('index : LSQUARE expression RSQUARE index')
    def index_expression(state, p):
        if len(p) == 4:
            return (p[1],) + p[3]
        return p[1],

    # -------------------- numthreads, threadid -------------------- #

    @pgen.production('threadid : THREADID')
    def threadid_threadid(state, p):
        return tree.ThreadID(hasmono=False)

    @pgen.production('numthreads : NUMTHREADS')
    def numthreads_numthreads(state, p):
        return tree.NumThreads(hasmono=False)

    @pgen.production('expression : threadid')
    @pgen.production('expression : numthreads')
    def expression_threadid(state, p):
        return p[0]

    # -------------------- names -------------------- #

    @pgen.production('name : NAME')
    @pgen.production('name : MONO NAME')
    def varfuncname_name(state, p):
        return ''.join(x.getstr() for x in p)

    # -------------------- string -------------------- #

    @pgen.production('string : STRING')
    def string_string(state, p):
        return p[0].getstr()[1:-1]

    # ------------- Generate final parsing method --------------- #

    _parser = pgen.build()

    def parse(filename):
        with open(filename, 'r') as f:
            source = f.read() + '\n'
        tokens = newlexer.lex(source)  # lexing.lexer.lex(source)
        try:
            state = ParserState(filename=filename, parser=_parser)
            return _parser.parse(tokens, state=state)
        except RailwaySyntaxError as e:
            sys.exit('\nSyntax Error of type ' +
                     type(e).__name__ + ':\n' +
                     e.args[0])
        except RplyParsingError as e:
            sourcepos = e.getsourcepos()
            if sourcepos is not None:
                lineno = e.getsourcepos().lineno
                marker = ' ' * (e.getsourcepos().colno - 1) + '^'
                sys.exit(
                    f'\nParsing Error\n File: {filename}\n Line: {lineno}\n\n' +
                    source.splitlines()[lineno - 1] + '\n' +
                    marker)
            sys.exit(f'Parsing error {e}')

    parsing_func_cache.append(parse)
    return parse

