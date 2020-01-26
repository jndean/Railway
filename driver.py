import struct
import sys

from interpreting import Fraction, RailwayException

from lexingparsing.lex import RailwayLexingError, tokenise
from lexingparsing.parse import RailwayParser, Token
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
                argv.append(Fraction(valuestr))
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
                [Fraction(struct.unpack(fmt, data[j: j+step])[0])
                 for j in range(0, len(data), step)]
            )
    return argv


def run_module(module, arguments):
    argv = parse_argv(arguments)
    try:
        module.main(argv)
    except RailwayException as e:
        sys.exit('\nCall Stack:\n-> ' +
                 '\n-> '.join(frame for frame in e.stack) +
                 '\nRuntime Error of type ' + type(e).__name__ + ':\n' +
                 e.message)


def parse_file(filename):
    with open(filename, 'r') as f:
        source_code = f.read()
    tokens = tokenise(source_code, TokenClass=Token)
    parser = RailwayParser(tokens)
    try:
        syntax_tree = parser.rule_module()
    except RailwayLexingError as e:
        line_num, col_num = e.args[0]-1, e.args[1]
        line = source_code.splitlines()[line_num]
        sys.exit(
            f'Lexing error in {filename} at line {line_num}, col {col_num}\n' +
            line + '\n' +
            ' ' * col_num + '^'
        )
    if syntax_tree is None:
        t = parser.tokens[-1]
        line = source_code.splitlines()[t.line-1]
        sys.exit(
            f'Parsing error in {filename} at line {t.line}, col {t.col}\n' +
            line + '\n' +
            ' ' * t.col + '^'
        )
    try:
        module = syntax_tree.compile()
    except RailwaySyntaxError as e:
        sys.exit(f'Syntax Error of type \n{type(e).__name__}\nMsg: {e.args[0]}')
    return module


def run():
    filename, *args = sys.argv[1:]
    module = parse_file(filename)
    run_module(module, args)
