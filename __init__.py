import struct
import sys

import interpreting as interpreter
from lexingparsing import lex, parse, AST
from lexingparsing.AST import RailwaySyntaxError


if __name__ == '__main__':
    program = AST.parse_file('tmp.rail')
    AST.run_module(program, ''.split())