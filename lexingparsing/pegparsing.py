from collections import namedtuple

Token = namedtuple("Token", ["type", "string", "line", "col"])


class BaseParser:
    def __init__(self, token_generator):
        self.gen = token_generator
        self.tokens = []
        self.token_pos = 0
        self.memos = {}

    def mark(self):
        return self.token_pos

    def reset(self, pos):
        self.token_pos = pos

    def peek_token(self):
        if self.token_pos == len(self.tokens):
            self.tokens.append(next(self.gen))
        return self.tokens[self.token_pos]

    def get_token(self):
        token = self.peek_token()
        self.token_pos += 1
        return token

    def expect(self, arg):
        token = self.peek_token()
        if token and token.type == arg:
            return self.get_token()
        return None

    def get_last_tokens(self, n=1):
        return self.tokens[-n:]


def memoise(func):
    def memoise_wrapper(self, *args):
        pos = self.mark()
        memo = self.memos.get(pos)
        if memo is None:
            memo = self.memos[pos] = {}
        key = (func, args)
        if key in memo:
            res, endpos = memo[key]
            self.reset(endpos)
        else:
            res = func(self, *args)
            endpos = self.mark()
            memo[key] = res, endpos
        return res
    return memoise_wrapper


def memoise_left_recursive(func):
    def memoise_left_rec_wrapper(self, *args):
        pos = self.mark()
        memo = self.memos.get(pos)
        if memo is None:
            memo = self.memos[pos] = {}
        key = (func, args)
        if key in memo:
            res, endpos = memo[key]
            self.reset(endpos)
        else:
            memo[key] = lastres, lastpos = None, pos
            while True:
                self.reset(pos)
                res = func(self, *args)
                endpos = self.mark()
                if endpos <= lastpos:
                    break
                memo[key] = lastres, lastpos = res, endpos
            res = lastres
            self.reset(lastpos)
        return res
    return memoise_left_rec_wrapper
