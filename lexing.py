import sys
from rply import LexerGenerator

__all__ = ["lexer"]

lg = LexerGenerator()

lg.add("IMPORT", r"import")
lg.add("AS", r"as")
lg.add("GLOBAL", r"global")
lg.add("LET", r"let")
lg.add("UNLET", r"unlet")
lg.add('FUNC', r"func")
lg.add('RETURN', r"return")
lg.add('PRINTLN', r"println")
lg.add('PRINT', r"print")
lg.add('IF', r"if")
lg.add('FI', r"fi")
lg.add('ELSE', r"else")
lg.add('LOOP', r"loop")
lg.add('POOL', r"pool")
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
lg.add('YRT', r"yrt")
lg.add('PROMOTE', 'promote')
lg.add('IN', r"in")
lg.add('TO', r"to")
lg.add('BY', r"by")
lg.add('TENSOR', r"tensor")
lg.add('BARRIER', r"barrier")
lg.add('MUTEX', r"mutex")
lg.add('XETUM', r"xetum")

lg.add("LRARROW", r"\<\=\>")
lg.add("LEQ", r"\<\=")
lg.add("GEQ", r"\>\=")
lg.add("NEQ", r"\!\=")
lg.add("EQ", r"\=\=")
lg.add("LESS", r"\<")
lg.add("GREAT", r"\>")

lg.add("RARROW", r"\=\>")
lg.add("MODADD", r"\+\=")
lg.add("MODSUB", r"\-\=")
lg.add("MODMUL", r"\*\=")
lg.add("MODDIV", r"\/\=")
lg.add("MODIDIV", r"\/\/\=")
lg.add("MODPOW", r"\*\*\=")
lg.add("MODMOD", r"\%\=")
lg.add("MODXOR", r"\^\=")
lg.add("MODOR", r"\|\=")
lg.add("MODAND", r"\&\=")
lg.add("ASSIGN", r"\=")

lg.add("ADD", r"\+")
lg.add("SUB", r"-")
lg.add("IDIV", r"\/\/")
lg.add("DIV", r"\/")
lg.add("POW", r"\*\*")
lg.add("MUL", r"\*")
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
lg.add("THREADID", r"TID")
lg.add("NUMTHREADS", r"#TID")
lg.add("MONO", r"\.")
lg.add("LEN", r"#")
lg.add("NOT", r"!")

lg.add("NUMBER", r"\d+(\/\d+)?")
lg.add("NAME", r"[a-zA-Z_][a-zA-Z0-9_.]*")
lg.add("STRING", r"\"[^\"]*\"")
lg.add("NEWLINE", r"\n[ \t\r\f\v\n]*")

# Escaped newlines
lg.ignore(r"\\[ \t\r\f\v]*\n")
# Whitespace
lg.ignore(r"[ \t\r\f\v]+")
# Comments
lg.ignore(r"\$[^\n]*\n+")
lg.ignore(r"\`[^`]*\`")

lexer = lg.build()


if __name__ == "__main__":
    with open(sys.argv[1], 'r') as f:
        for t in lexer.lex(f.read()):
            print(t)
