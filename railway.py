import struct
import sys

import rply

import interpreting
from interpreting import Fraction, RailwayException
from lexing import lexer
import parsing
from parsing import generate_parsing_function, RailwaySyntaxError


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
            argv.append([Fraction(struct.unpack(fmt, data[j: j+step])[0])
                         for j in range(0, len(data), step)])
    return argv


if __name__ == '__main__':

    filename = sys.argv[1]
    argv = parse_argv(sys.argv[2:])
    parse = generate_parsing_function(tree=interpreting)
    program = parse(filename)
    try:
        program.main(argv)
    except RailwayException as e:
        sys.exit('\nCall Stack:\n-> ' +
                 '\n-> '.join(frame for frame in e.stack) +
                 '\nRuntime Error of type ' + type(e).__name__ + ':\n' +
                 e.message)
