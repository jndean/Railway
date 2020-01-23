import struct
import sys

import interpreting as interpreter
from lexingparsing import lex, parse
from lexingparsing.AST import RailwaySyntaxError


def parse_argv(args):
    if len(args) % 2:
        sys.exit('Odd number of arguments. They should come in type-value '
                 'pairs, e.g. "-i32 filename"')
    flag_format_codes = {'-n': None,
                         '-f32': 'f', '-f64': 'd',
                         '-i8': 'b', '-i16': 'h', '-i32': 'i', '-i64': 'q',
                         '-u8': 'B', '-u16': 'H', '-u32': 'I', '-u64': 'Q'}
    argv = []
    for i in range(0, len(args), 2):
        flag, valuestr = args[i:i+2]
        if flag not in flag_format_codes:
            sys.exit(f'Unrecognised argument type flag: {flag}')
        if flag == '-n':
            try:
                argv.append(interpreter.Fraction(valuestr))
            except ValueError:
                sys.exit(f'"{valuestr}" cannot be interpreted as a number')
        else:
            try:
                with open(valuestr, 'rb') as _file:
                    data = _file.read()
            except FileNotFoundError:
                sys.exit(f'File "{valuestr}" not found')
            step = int(flag[2:]) // 8
            if len(data) % step:
                sys.exit(f'File "{valuestr}" is the wrong length to be an array'
                         f'of type {flag[1:]}')
            fmt = flag_format_codes[flag]
            argv.append(
                [interpreter.Fraction(struct.unpack(fmt, data[j: j+step])[0])
                 for j in range(0, len(data), step)]
            )
    return argv


def gen_error_msg(err_type, filename, line_num, col_num):
    with open(filename, 'r') as f:
        line = f.readlines()[line_num-1]
    ret = f'{err_type} error in {filename} at line {line_num}, col {col_num}\n'
    ret += line
    ret += ' ' * (col_num - 1) + '^'
    return ret


if __name__ == '__main__':
    sys.argv = 'r tmp.rail'.split()

    _, filename, *arguments = sys.argv
    with open(filename, 'r') as f:
        tokens = lex.tokenise(f.read(), TokenClass=parse.Token)

    parser = parse.RailwayParser(tokens)
    try:
        syntax_tree = parser.rule_module()
    except lex.RailwayLexingError as e:
        sys.exit(gen_error_msg('Lexing', filename, e.args[0], e.args[1]+1))
    if syntax_tree is None:
        t = parser.tokens[-1]
        sys.exit(gen_error_msg('Parsing', filename, t.line, t.col))

    try:
        program = syntax_tree.compile()
    except RailwaySyntaxError as e:
        sys.exit(f'Syntax Error of type \n{type(e).__name__}\nMsg: {e.args[0]}')

    argv = parse_argv(arguments)
    try:
        program.main(argv)
    except interpreter.RailwayException as e:
        sys.exit('\nCall Stack:\n-> ' +
                 '\n-> '.join(frame for frame in e.stack) +
                 '\nRuntime Error of type ' + type(e).__name__ + ':\n' +
                 e.message)
