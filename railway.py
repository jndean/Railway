import sys

import interpreting
from lexing import lexer
from parsing import generate_parser


if __name__ == '__main__':
    with open(sys.argv[1], 'r') as f:
        file = f.read()
    prog = generate_parser(tree=interpreting).parse(lexer.lex(file))
    prog.eval()
