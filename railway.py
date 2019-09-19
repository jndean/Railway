import sys

import rply

import interpreting
from lexing import lexer
from parsing import generate_parsing_function, RailwaySyntaxError


if __name__ == '__main__':

    filename = sys.argv[1]
    with open(filename, 'r') as f:
        source = f.read() + '\n'
    tokens = lexer.lex(source)
    parse = generate_parsing_function(tree=interpreting)

    try:
        program = parse(tokens, filename)
    except RailwaySyntaxError as e:
        sys.exit('\nSyntax Error of type ' +
                 type(e).__name__ + ':\n' +
                 e.args[0])
    except rply.ParsingError as e:
        sourcepos = e.getsourcepos()
        if sourcepos is not None:
            lineno = e.getsourcepos().lineno
            marker = ' ' * (e.getsourcepos().colno - 1) + '^'
            sys.exit(f'\nParsing Error\n File: {filename}\n Line: {lineno}\n\n' +
                     source.splitlines()[lineno-1] + '\n' +
                     marker)
        sys.exit(f'Parsing error {e}')

    try:
        program.main()
    except interpreting.RailwayException as e:
        sys.exit('\nCall Stack:\n-> ' +
                 '\n-> '.join(frame for frame in e.stack) +
                 '\nRuntime Error of type ' + type(e).__name__ + ':\n' +
                 e.message)
