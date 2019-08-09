import sys
from rply import LexerGenerator

__all__ = ["lexer", "all_tokens"]

all_tokens = [
    "IMPORT", "AS", "GLOBAL", "FILE", "LET", "UNLET", 'FUNC',
    'RETURN', 'PRINT', 'IF', 'FI', 'ELSE', 'LOOP', 'WHILE',
    'FOR', 'ROF', 'CALL', 'UNCALL', 'DO', 'UNDO', 'YIELD',
    'SWAP', 'PUSH', 'POP', 'TRY', 'CATCH', 'IN', "LEQ", "GEQ",
    "NEQ", "EQ", "LESS", "GREAT", "LRARROW", "RARROW",
    "MODADD", "MODSUB", "MODMUL", "MODDIV", "ADD", "SUB",
    "IDIV", "DIV", "MUL", "POW", "MOD", "XOR", "OR", "AND",
    "LPAREN", "RPAREN", "LSQUARE", "RSQUARE", "LBRACK",
    "RBRACK", "COMMA", "MONO", "LEN", "NOT", "SWITCH", "NUMBER",
    "NAME", "STRING", "COMMENT", "NEWLINE"]

lg = LexerGenerator()

lg.add("IMPORT", r"import")
lg.add("AS", r"as")
lg.add("GLOBAL", r"global")
lg.add("FILE", r"file")
lg.add("LET", r"let")
lg.add("UNLET", r"unlet")
lg.add('FUNC', r"func")
lg.add('RETURN', r"return")
lg.add('PRINT', r"print")
lg.add('IF', r"if")
lg.add('FI', r"fi")
lg.add('ELSE', r"else")
lg.add('LOOP', r"loop")
lg.add('WHILE', r"while")
lg.add('FOR', r"for")
lg.add('ROF', r"rof")
lg.add('CALL', r"call")
lg.add('UNCALL', r"uncall")
lg.add('DO', r"do")
lg.add('UNDO', r"undo")
lg.add('YIELD', r"yield")
lg.add('SWAP', r"swap")
lg.add('PUSH', r"push")
lg.add('POP', r"pop")
lg.add('TRY', r"try")
lg.add('CATCH', r"catch")
lg.add('IN', r"in")

lg.add("LEQ", r"\<\=")
lg.add("GEQ", r"\>\=")
lg.add("NEQ", r"\!\=")
lg.add("EQ", r"\=")
lg.add("LESS", r"\<")
lg.add("GREAT", r"\>")

lg.add("LRARROW", r"\<\=\>")
lg.add("RARROW", r"\=\>")
lg.add("MODADD", r"\+\=")
lg.add("MODSUB", r"\-\=")
lg.add("MODMUL", r"\*\=")
lg.add("MODDIV", r"\/\=")

lg.add("ADD", r"\+")
lg.add("SUB", r"-")
lg.add("IDIV", r"\/\/")
lg.add("DIV", r"\/")
lg.add("MUL", r"\*")
lg.add("POW", r"\*\*")
lg.add("MOD", r"\%")

lg.add("XOR", r"\^")
lg.add("OR", r"\|")
lg.add("AND", r"\&")

lg.add("LPAREN", r"\(")
lg.add("RPAREN", r"\)")
lg.add("LSQUARE", r"\[")
lg.add("RSQUARE", r"\]")
lg.add("LBRACK", r"\{")
lg.add("RBRACK", r"\}")
lg.add("COMMA", r"\,")

# Symbols with special meaning
lg.add("MONO", r"\.")
lg.add("LEN", r"#")
lg.add("NOT", r"!")
lg.add("SWITCH", r"~")

lg.add("NUMBER", r"\d+(\/\d+)?")
lg.add("NAME", r"[a-zA-Z][a-zA-Z0-9_.]*")
lg.add("STRING", r"\"[^\"]*\"")
lg.add("COMMENT", r"%[^%]*%")
lg.add("NEWLINE", r"\n")

# Escape newlines
lg.ignore(r"\\[ \t\r\f\v]*\n")
# Whitespace
lg.ignore(r"[ \t\r\f\v]+")

lexer = lg.build()

if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        for t in lexer.lex(f.read()):
            print(t)
