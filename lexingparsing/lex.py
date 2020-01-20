from collections import namedtuple
import re


class RailwayLexingError(RuntimeError):
    def __init__(self, line, col):
        self.line, self.col = line, col


name_regex = re.compile(r'[a-zA-Z_][a-zA-Z0-9_.]*')
number_regex = re.compile('\d+(\/\d+)?')
string_regex = re.compile('("[^"]*")|(\'[^\']*\')')
escaped_newline_regex = re.compile('\\\\[ \t\r\f\v]*\n')
ignore_regex = re.compile('([$][^$]*[$])|([ \t\r\f\v]+)')
symbols = {
    'import', 'as', 'global', 'let', 'unlet', 'func', 'return', 'println',
    'print', 'if', 'fi', 'else', 'loop', 'pool', 'for', 'rof', 'call', 'uncall',
    'do', 'undo', 'yield', 'swap', 'push', 'pop', 'try', 'catch', 'yrt',
    'promote', 'in', 'to', 'by', 'tensor', 'barrier', 'mutex', 'xetum',
    'TID', '#TID',
    '<=>', '<=', '=>', '>=', '!=', '==',
    '//=', '**=', '+=', '-=', '*=', '/=', '%=', '^=', '|=', '&=',
    '//', '**', '<', '>', '=', '+', '-', '*', '/', '%', '^', '|', '&',
    '(', ')', '[', ']', '{', '}', ',', '.', '#', '!'
}

max_symbol_length = max(len(s) for s in symbols)

DefaultToken = namedtuple('Token', ['type', 'string', 'line', 'col'])


def tokenise(data, TokenClass=DefaultToken):
    line, col = 1, 0
    pos = 0
    skip_newline = True

    len_data = len(data)
    while pos < len_data:

        if data[pos] == '\n':
            if not skip_newline:
                yield TokenClass('NEWLINE', '\n', line, col)
            skip_newline = True
            line += 1
            col = 0
            pos += 1
            continue

        for sym_length in range(min(max_symbol_length, len_data - pos), 0, -1):
            if data[pos:pos + sym_length] in symbols:
                endpos = pos + sym_length
                string = data[pos:endpos]
                yield TokenClass(string, string, line, col)
                skip_newline = False
                col += sym_length
                pos = endpos
                break
        else:
            name_match = name_regex.match(data, pos)
            if name_match:
                endpos = name_match.span()[1]
                string = data[pos:endpos]
                yield TokenClass('NAME', string, line, col)
                skip_newline = False
                col += endpos - pos
                pos = endpos
                continue

            number_match = number_regex.match(data, pos)
            if number_match:
                endpos = number_match.span()[1]
                string = data[pos:endpos]
                yield TokenClass('NUMBER', string, line, col)
                skip_newline = False
                col += endpos - pos
                pos = endpos
                continue

            string_match = string_regex.match(data, pos)
            if string_match:
                endpos = string_match.span()[1]
                string = data[pos+1:endpos-1]
                yield TokenClass('STRING', string, line, col)
                skip_newline = False
                col += endpos - pos
                pos = endpos
                continue

            ignore_match = ignore_regex.match(data, pos)
            if ignore_match:
                endpos = ignore_match.span()[1]
                line += data[pos:endpos].count('\n')
                col += endpos - pos
                pos = endpos
                continue

            escaped_newline_match = escaped_newline_regex.match(data, pos)
            if escaped_newline_match:
                line += 1
                col = 0
                pos = escaped_newline_match.span()[1]
                continue

            raise RailwayLexingError(line, col)

    if not skip_newline:
        yield TokenClass('NEWLINE', '\n', line, col)
    yield TokenClass('ENDMARKER', '', line, col)


if __name__ == '__main__':
    with open('tmp.rail') as f:
        for token in tokenise(f.read()):
            print(f'{repr(token.string):12s}: {token.type}')