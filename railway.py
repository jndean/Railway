import sys

import rply

import interpreting
import lexing
import parsing


if __name__ == '__main__':
    filename = sys.argv[1]
    with open(filename, 'r') as f:
        source = f.read()
    tokens = lexing.lexer.lex(source)
    parser = parsing.generate_parser(tree=interpreting)
    try:
        program = parser.parse(tokens)
    except parsing.RailwaySyntaxError as e:
        sys.exit('\nSyntax Error of type ' +
                 type(e).__name__ + ':\n' +
                 e.args[0])
    except rply.ParsingError as e:
        lineno = e.getsourcepos().lineno
        marker = ' ' * (e.getsourcepos().colno - 1) + '^'
        sys.exit(f'\nParsing Error\n File: {filename}\n Line: {lineno}\n\n' +
                 source.splitlines()[lineno-1] + '\n' +
                 marker)
    try:
        program.eval()
    except interpreting.RailwayException as e:
        sys.exit('\nCall Stack:\n-> ' +
                 '\n-> '.join(frame for frame in e.stack) +
                 '\nRuntime Error of type ' + type(e).__name__ + ':\n' +
                 e.message)
