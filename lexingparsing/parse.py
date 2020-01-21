# This file was generated from the grammar file grammar.peg #
from .pegparsing import BaseParser, memoise, memoise_left_recursive
from .AST import (
    Token, ThreadID, NumThreads, Lookup, Length, Uniop, Binop, ArrayLiteral,
    ArrayTensor, ArrayRange, Let, Unlet, Promote, Pop, Push, Swap, If, Loop,
    For, Barrier, Mutex, Modop, Print, PrintLn, DoUndo, Catch, Try,
    CallBlock, Parameter, Call, Function, Global, Import, Module, Fraction
)


class RailwayParser(BaseParser):

    @memoise
    def rule_0(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_import()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_global()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_func_decl()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_repetition1(self):
        result = []
        while (item := self.rule_0()) is not None:
            result.append(item)
        return result

    @memoise
    def rule_module(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_repetition1()) is not None)
            and ((t1 := self.expect('ENDMARKER')) is not None)
        ):
            return Module(t0)
        self.reset(pos)

        return None

    @memoise
    def rule_3(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('as')) is not None)
            and ((t1 := self.rule_name()) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_import(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('import')) is not None)
            and ((t1 := self.expect('STRING')) is not None)
            and (((t2 := self.rule_3()) is not None) or True)
            and ((t3 := self.expect('NEWLINE')) is not None)
        ):
            return Import(t1, t2)
        self.reset(pos)

        return None

    @memoise
    def rule_5(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('=')) is not None)
            and ((t1 := self.rule_expression()) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_global(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('global')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and (((t2 := self.rule_5()) is not None) or True)
            and ((t3 := self.expect('NEWLINE')) is not None)
        ):
            return Global(t1, t2)
        self.reset(pos)

        return None

    @memoise
    def rule_repetition7(self):
        result = []
        while (item := self.rule_statement()) is not None:
            result.append(item)
        return result

    @memoise
    def rule_func_decl(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('func')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and ((t2 := self.rule_param_tuple()) is not None)
            and ((t3 := self.rule_param_tuple()) is not None)
            and ((t4 := self.expect('NEWLINE')) is not None)
            and ((t5 := self.rule_repetition7()) is not None)
            and ((t6 := self.expect('return')) is not None)
            and ((t7 := self.rule_param_tuple()) is not None)
            and ((t8 := self.expect('NEWLINE')) is not None)
        ):
            return Function(t1, t2, t3, t5, t7)
        self.reset(pos)

        return None

    @memoise
    def rule_9(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_let_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_unlet_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_promote_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_swap_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_push_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_pop_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_if_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_loop_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_for_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_modify_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_barrier_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_mutex_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_print_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_doundo_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_try_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_catch_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_call_stmt()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_statement(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_9()) is not None)
            and ((t1 := self.expect('NEWLINE')) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_11(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_param_tuple()) is not None)
            and ((t1 := self.expect('=>')) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_repeat12(self):

        ret = [self.rule_call_block()]
        if ret[0] is None:
            return []
        pos = self.mark()
        while True:
            if (self.expect('=>') is None) or ((item := self.rule_call_block()) is None):
                break
            ret.append(item)
            pos = self.mark()
        self.reset(pos)
        return ret

    @memoise
    def rule_13(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_repeat12()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_14(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('=>')) is not None)
            and ((t1 := self.rule_param_tuple()) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_15(self):
        pos = self.mark()
        if (True
            and (((t0 := self.rule_11()) is not None) or True)
            and ((t1 := self.rule_13()) is not None)
            and (((t2 := self.rule_14()) is not None) or True)
        ):
            return Call(t0, t1, t2)
        self.reset(pos)

        return None

    @memoise
    def rule_16(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_param_tuple()) is not None)
            and ((t1 := self.expect('<=')) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_repeat17(self):

        ret = [self.rule_call_block()]
        if ret[0] is None:
            return []
        pos = self.mark()
        while True:
            if (self.expect('<=') is None) or ((item := self.rule_call_block()) is None):
                break
            ret.append(item)
            pos = self.mark()
        self.reset(pos)
        return ret

    @memoise
    def rule_18(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_repeat17()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_19(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('<=')) is not None)
            and ((t1 := self.rule_param_tuple()) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_20(self):
        pos = self.mark()
        if (True
            and (((t0 := self.rule_16()) is not None) or True)
            and ((t1 := self.rule_18()) is not None)
            and (((t2 := self.rule_19()) is not None) or True)
        ):
            return Call(t2, t1, t0)
        self.reset(pos)

        return None

    @memoise
    def rule_greedy21(self):

        start_pos = self.mark()
        lhs = self.rule_15()
        lhs_pos = self.mark()
        self.reset(start_pos)
        rhs = self.rule_20()
        rhs_pos = self.mark()
        if lhs_pos > rhs_pos:
            self.reset(lhs_pos)
            return lhs
        return rhs

    @memoise
    def rule_call_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_greedy21()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_23(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('call')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('uncall')) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_24(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('{')) is not None)
            and ((t1 := self.rule_expression()) is not None)
            and ((t2 := self.expect('}')) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_call_block(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_23()) is not None)
            and ((t1 := self.rule_name()) is not None)
            and (((t2 := self.rule_24()) is not None) or True)
            and ((t3 := self.rule_param_tuple()) is not None)
        ):
            return CallBlock(t0, t1, t2, t3)
        self.reset(pos)

        return None

    @memoise
    def rule_repeat26(self):

        ret = [self.rule_parameter()]
        if ret[0] is None:
            return []
        pos = self.mark()
        while True:
            if (self.expect(',') is None) or ((item := self.rule_parameter()) is None):
                break
            ret.append(item)
            pos = self.mark()
        self.reset(pos)
        return ret

    @memoise
    def rule_param_tuple(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('(')) is not None)
            and ((t1 := self.rule_repeat26()) is not None)
            and ((t2 := self.expect(')')) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_try_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('try')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_name()) is not None)
            and ((t3 := self.expect('in')) is not None)
            and ((t4 := self.rule_expression()) is not None)
            and ((t5 := self.expect(')')) is not None)
            and ((t6 := self.expect('NEWLINE')) is not None)
            and ((t7 := self.rule_repetition7()) is not None)
            and ((t8 := self.expect('yrt')) is not None)
        ):
            return Try(t2, t4, t7)
        self.reset(pos)

        return None

    @memoise
    def rule_catch_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('catch')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_expression()) is not None)
            and ((t3 := self.expect(')')) is not None)
        ):
            return Catch(t2)
        self.reset(pos)

        return None

    @memoise
    def rule_30(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('yield')) is not None)
            and ((t1 := self.expect('NEWLINE')) is not None)
            and ((t2 := self.rule_repetition7()) is not None)
        ):
            return t2
        self.reset(pos)

        return None

    @memoise
    def rule_doundo_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('do')) is not None)
            and ((t1 := self.expect('NEWLINE')) is not None)
            and ((t2 := self.rule_repetition7()) is not None)
            and (((t3 := self.rule_30()) is not None) or True)
            and ((t4 := self.expect('undo')) is not None)
        ):
            return DoUndo(t2, t3)
        self.reset(pos)

        return None

    @memoise
    def rule_32(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('STRING')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expression()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_repeat33(self):

        ret = [self.rule_32()]
        if ret[0] is None:
            return []
        pos = self.mark()
        while True:
            if (self.expect(',') is None) or ((item := self.rule_32()) is None):
                break
            ret.append(item)
            pos = self.mark()
        self.reset(pos)
        return ret

    @memoise
    def rule_print_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('print')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_repeat33()) is not None)
            and ((t3 := self.expect(')')) is not None)
        ):
            return Print(t2)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('println')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_repeat33()) is not None)
            and ((t3 := self.expect(')')) is not None)
        ):
            return PrintLn(t2)
        self.reset(pos)

        return None

    @memoise
    def rule_barrier_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('barrier')) is not None)
            and ((t1 := self.expect('STRING')) is not None)
        ):
            return Barrier(t1.string)
        self.reset(pos)

        return None

    @memoise
    def rule_mutex_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('mutex')) is not None)
            and ((t1 := self.expect('STRING')) is not None)
            and ((t2 := self.expect('NEWLINE')) is not None)
            and ((t3 := self.rule_repetition7()) is not None)
            and ((t4 := self.expect('xetum')) is not None)
        ):
            return Mutex(t1.string, t3)
        self.reset(pos)

        return None

    @memoise
    def rule_modify_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_lookup()) is not None)
            and ((t1 := self.rule_modop_symbol()) is not None)
            and ((t2 := self.rule_expression()) is not None)
        ):
            return Modop(t0, t1, t2)
        self.reset(pos)

        return None

    @memoise
    def rule_for_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('for')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_expression()) is not None)
            and ((t3 := self.expect('in')) is not None)
            and ((t4 := self.rule_expression()) is not None)
            and ((t5 := self.expect(')')) is not None)
            and ((t6 := self.expect('NEWLINE')) is not None)
            and ((t7 := self.rule_repetition7()) is not None)
            and ((t8 := self.expect('rof')) is not None)
        ):
            return For(t2, t4, t7)
        self.reset(pos)

        return None

    @memoise
    def rule_loop_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('loop')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_expression()) is not None)
            and ((t3 := self.expect(')')) is not None)
            and ((t4 := self.expect('NEWLINE')) is not None)
            and ((t5 := self.rule_repetition7()) is not None)
            and ((t6 := self.expect('pool')) is not None)
            and ((t7 := self.expect('(')) is not None)
            and (((t8 := self.rule_expression()) is not None) or True)
            and ((t9 := self.expect(')')) is not None)
        ):
            return Loop(t2, t5, t8)
        self.reset(pos)

        return None

    @memoise
    def rule_40(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('else')) is not None)
            and ((t1 := self.expect('NEWLINE')) is not None)
            and ((t2 := self.rule_repetition7()) is not None)
        ):
            return t2
        self.reset(pos)

        return None

    @memoise
    def rule_if_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('if')) is not None)
            and ((t1 := self.expect('(')) is not None)
            and ((t2 := self.rule_expression()) is not None)
            and ((t3 := self.expect(')')) is not None)
            and ((t4 := self.expect('NEWLINE')) is not None)
            and ((t5 := self.rule_repetition7()) is not None)
            and (((t6 := self.rule_40()) is not None) or True)
            and ((t7 := self.expect('fi')) is not None)
            and ((t8 := self.expect('(')) is not None)
            and (((t9 := self.rule_expression()) is not None) or True)
            and ((t10 := self.expect(')')) is not None)
        ):
            return If(t2, t5, t6, t9)
        self.reset(pos)

        return None

    @memoise
    def rule_pop_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('pop')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
            and ((t2 := self.expect('=>')) is not None)
            and ((t3 := self.rule_lookup()) is not None)
        ):
            return Pop(t1, t3)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('pop')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
            and ((t2 := self.expect('<=')) is not None)
            and ((t3 := self.rule_lookup()) is not None)
        ):
            return Pop(t3, t1)
        self.reset(pos)

        return None

    @memoise
    def rule_push_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('push')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
            and ((t2 := self.expect('=>')) is not None)
            and ((t3 := self.rule_lookup()) is not None)
        ):
            return Push(t1, t3)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('push')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
            and ((t2 := self.expect('<=')) is not None)
            and ((t3 := self.rule_lookup()) is not None)
        ):
            return Push(t3, t1)
        self.reset(pos)

        return None

    @memoise
    def rule_swap_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('swap')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
            and ((t2 := self.expect('<=>')) is not None)
            and ((t3 := self.rule_lookup()) is not None)
        ):
            return Swap(t1, t3)
        self.reset(pos)

        return None

    @memoise
    def rule_promote_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('promote')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and ((t2 := self.expect('=>')) is not None)
            and ((t3 := self.rule_name()) is not None)
        ):
            return Promote(t1, t3)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('promote')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and ((t2 := self.expect('<=')) is not None)
            and ((t3 := self.rule_name()) is not None)
        ):
            return Promote(t3, t1)
        self.reset(pos)

        return None

    @memoise
    def rule_let_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('let')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and (((t2 := self.rule_5()) is not None) or True)
        ):
            return Let(t1, t2)
        self.reset(pos)

        return None

    @memoise
    def rule_unlet_stmt(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('unlet')) is not None)
            and ((t1 := self.rule_name()) is not None)
            and (((t2 := self.rule_5()) is not None) or True)
        ):
            return Unlet(t1, t2)
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expression(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expression()) is not None)
            and ((t1 := self.expect('|')) is not None)
            and ((t2 := self.rule_expr0()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr0()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr0(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr0()) is not None)
            and ((t1 := self.expect('&')) is not None)
            and ((t2 := self.rule_expr1()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr1()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr1(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr1()) is not None)
            and ((t1 := self.expect('^')) is not None)
            and ((t2 := self.rule_expr2()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr2()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_51(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('<')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('<=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('>')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('>=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('==')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('!=')) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr2(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr2()) is not None)
            and ((t1 := self.rule_51()) is not None)
            and ((t2 := self.rule_expr3()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr3()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr3(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr3()) is not None)
            and ((t1 := self.expect('+')) is not None)
            and ((t2 := self.rule_expr4()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr3()) is not None)
            and ((t1 := self.expect('-')) is not None)
            and ((t2 := self.rule_expr4()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr4()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr4(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr4()) is not None)
            and ((t1 := self.expect('*')) is not None)
            and ((t2 := self.rule_expr5()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr4()) is not None)
            and ((t1 := self.expect('/')) is not None)
            and ((t2 := self.rule_expr5()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr4()) is not None)
            and ((t1 := self.expect('//')) is not None)
            and ((t2 := self.rule_expr5()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr4()) is not None)
            and ((t1 := self.expect('%')) is not None)
            and ((t2 := self.rule_expr5()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_expr5()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise_left_recursive
    def rule_expr5(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_expr5()) is not None)
            and ((t1 := self.expect('**')) is not None)
            and ((t2 := self.rule_atom()) is not None)
        ):
            return Binop(t0, t1, t2)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_atom()) is not None)
        ):
            return t0
        self.reset(pos)

        return None

    @memoise
    def rule_atom(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('(')) is not None)
            and ((t1 := self.rule_expression()) is not None)
            and ((t2 := self.expect(')')) is not None)
        ):
            return t1
        self.reset(pos)

        if (True
            and ((t0 := self.rule_array_literal()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_array_tensor()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_array_range()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_lookup()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('NUMBER')) is not None)
        ):
            return Fraction(t0.string)
        self.reset(pos)

        if (True
            and ((t0 := self.rule_threadid()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.rule_numthreads()) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('-')) is not None)
            and ((t1 := self.rule_atom()) is not None)
        ):
            return Uniop(t0, t1)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('!')) is not None)
            and ((t1 := self.rule_atom()) is not None)
        ):
            return Uniop(t0, t1)
        self.reset(pos)

        if (True
            and ((t0 := self.expect('#')) is not None)
            and ((t1 := self.rule_lookup()) is not None)
        ):
            return Length(t1)
        self.reset(pos)

        return None

    @memoise
    def rule_repeat57(self):

        ret = [self.rule_expression()]
        if ret[0] is None:
            return []
        pos = self.mark()
        while True:
            if (self.expect(',') is None) or ((item := self.rule_expression()) is None):
                break
            ret.append(item)
            pos = self.mark()
        self.reset(pos)
        return ret

    @memoise
    def rule_array_literal(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('[')) is not None)
            and ((t1 := self.rule_repeat57()) is not None)
            and ((t2 := self.expect(']')) is not None)
        ):
            return ArrayLiteral(t1)
        self.reset(pos)

        return None

    @memoise
    def rule_59(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('by')) is not None)
            and ((t1 := self.rule_expression()) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_array_range(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('[')) is not None)
            and ((t1 := self.rule_expression()) is not None)
            and ((t2 := self.expect('to')) is not None)
            and ((t3 := self.rule_expression()) is not None)
            and (((t4 := self.rule_59()) is not None) or True)
            and ((t5 := self.expect(']')) is not None)
        ):
            return ArrayRange(t1, t3, t4)
        self.reset(pos)

        return None

    @memoise
    def rule_array_tensor(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('[')) is not None)
            and ((t1 := self.rule_expression()) is not None)
            and ((t2 := self.expect('tensor')) is not None)
            and ((t3 := self.rule_expression()) is not None)
            and ((t4 := self.expect(']')) is not None)
        ):
            return ArrayTensor(t1, t3)
        self.reset(pos)

        return None

    @memoise
    def rule_62(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('[')) is not None)
            and ((t1 := self.rule_expression()) is not None)
            and ((t2 := self.expect(']')) is not None)
        ):
            return t1
        self.reset(pos)

        return None

    @memoise
    def rule_repetition63(self):
        result = []
        while (item := self.rule_62()) is not None:
            result.append(item)
        return result

    @memoise
    def rule_lookup(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_name()) is not None)
            and ((t1 := self.rule_repetition63()) is not None)
        ):
            return Lookup(name=t0, index=tuple(t1))
        self.reset(pos)

        return None

    @memoise
    def rule_parameter(self):
        pos = self.mark()
        if (True
            and ((t0 := self.rule_name()) is not None)
        ):
            return Parameter(t0)
        self.reset(pos)

        return None

    @memoise
    def rule_threadid(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('TID')) is not None)
        ):
            return ThreadID()
        self.reset(pos)

        return None

    @memoise
    def rule_numthreads(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('#TID')) is not None)
        ):
            return NumThreads()
        self.reset(pos)

        return None

    @memoise
    def rule_name(self):
        pos = self.mark()
        if (True
            and (((t0 := self.expect('.')) is not None) or True)
            and ((t1 := self.expect('NAME')) is not None)
        ):
            return ('.' if t0 is not None else '') + t1.string
        self.reset(pos)

        return None

    @memoise
    def rule_modop_symbol(self):
        pos = self.mark()
        if (True
            and ((t0 := self.expect('+=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('-=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('*=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('/=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('//=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('**=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('%=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('^=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('|=')) is not None)
        ):
            return t0
        self.reset(pos)

        if (True
            and ((t0 := self.expect('&=')) is not None)
        ):
            return t0
        self.reset(pos)

        return None