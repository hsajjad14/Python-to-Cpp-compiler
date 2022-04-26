#!/usr/bin/env python3

import argparse
from ply import lex

# List of token names. This is always required
tokens = [
    'EQUAL_ASSIGN',
    'L_PARENTHESE',
    'R_PARENTHESE',
    'L_BRACKET',
    'R_BRACKET',
    'DOT',
    'RIGHT_ARROW',

    'PLUS',
    'MINUS',
    'MULTIPLY',
    'DIVIDE',
    'POWER',
    'AND_BITWISE',
    'OR_BITWISE',
    'EQUALS',
    'NOT_EQUALS',
    'LESS_THAN',
    'LESS_THAN_OR_EQ',
    'GREATER_THAN',
    'GREATER_THAN_OR_EQ',
    'COMMA',
    'COLON',
    'DIGIT',
    'ID',

    'STRING_LITERAL',

    'TAB',
    'NEWLINE',
    'INDENT',
    'DEDENT'
]

# Reserved words which should not match any IDs
reserved = {
    'int':      'INT',
    'str':      'STRING',
    'float':    'FLOAT',
    'bool':     'BOOLEAN',
    'list':     'LIST',
    'not':      'NOT',
    'import':   'IMPORT',
    'break':    'BREAK',
    'continue': 'CONTINUE',
    'if':       'IF',
    'else':     'ELSE',
    'elif':     'ELSE_IF',
    'while':    'WHILE',
    'for':      'FOR',
    'in':       'IN',
    'range':    'RANGE',
    'pass':     'PASS',
    'return':   'RETURN',
    'def':      'METHOD_DEF',
    'class':    'CLASS',
    'self':     'SELF',
    'True':     'TRUE',
    'False':    'FALSE',

    'and':      'AND',
    'or':       'OR',
    'len':      'LEN',
    "from":     'FROM',
    "len":      'LEN'
}

# Add reserved names to list of tokens
tokens += list(reserved.values())

class pythonLexer():

    # A string containing ignored characters (only spaces)
    t_ignore = ' '

    # Regular expression rule with some action code
    t_EQUAL_ASSIGN = r'='
    t_L_PARENTHESE = r'\('
    t_R_PARENTHESE = r'\)'
    t_L_BRACKET = r'\['
    t_R_BRACKET = r'\]'
    t_DOT = r'\.'
    t_RIGHT_ARROW = r'->'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_MULTIPLY = r'\*'
    t_DIVIDE = r'/'
    t_POWER = r'\*\*'
    t_AND_BITWISE = r'&'
    t_OR_BITWISE = r'\|'
    t_EQUALS = r'\=\='
    t_NOT_EQUALS = r'!\='
    t_LESS_THAN = r'<'
    t_LESS_THAN_OR_EQ = r'<\='
    t_GREATER_THAN = r'>'
    t_GREATER_THAN_OR_EQ = r'>\='
    t_COMMA = r','
    t_COLON = r':'
    t_TAB = r'\t'
    t_STRING_LITERAL = r'\".*\"|\'.*\''

    # Indent/Dedent Tracking
    filtered_tokens = []
    indent_levels = [0]
    indent_counter = 0
    newline_seen = False

    def t_DIGIT(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z_0-9]*'
        t.type = reserved.get(t.value, 'ID') # Check for reserved words
        return t

    # Rule to track line numbers
    def t_NEWLINE(self, t):
        r'\n'
        t.lexer.lineno += len(t.value)
        t.type = 'NEWLINE'
        return t

    # Rule for error handling
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    def __init__(self, **kwargs):
        self.tokens = tokens
        self.lexer = lex.lex(module=self, **kwargs)

    def generate_token(self, type, token):
        tok = lex.LexToken()
        tok.value = None
        tok.type = type
        tok.lineno = token.lineno
        tok.lexpos = token.lexpos
        return tok

    def INDENT(self, token):
        return self.generate_token("INDENT", token)

    def DEDENT(self, token):
        return self.generate_token("DEDENT", token)

    def indentation_filter(self, token):
        if token.type == 'NEWLINE':
            self.indent_counter = 0
            if self.newline_seen:
                return
            else:
                self.newline_seen = True
                self.filtered_tokens.append(token)
                return

        self.newline_seen = False

        if (token.type != 'TAB' and token.type != 'NEWLINE'):
            if self.indent_counter > self.indent_levels[-1]:
                self.indent_levels.append(self.indent_counter)
                self.filtered_tokens.append(self.INDENT(token))
            else:
                while self.indent_counter < self.indent_levels[-1]:
                    self.filtered_tokens.append(self.DEDENT(token))
                    self.indent_levels.pop()
            self.filtered_tokens.append(token)
            return

        if token.type == 'TAB':
            self.indent_counter += 1

    def filter_stream(self, data):
        self.lexer.input(data)
        while True:
            token = self.lexer.token()
            if not token:
                break
            self.indentation_filter(token)

        # DEDENT remaining levels
        while len(self.indent_levels) > 1:
            self.filtered_tokens.append(self.DEDENT(self.filtered_tokens[-1]))
            self.indent_levels.pop()

        for token in self.filtered_tokens:
            yield token

class IndentLexer():
    def __init__(self):
        self.lexer = pythonLexer()
        self.token_stream = None

    def build(self, **kwargs):
        self.lexer = pythonLexer()
        self.token_stream = None

    def input(self, data):
        self.token_stream = self.lexer.filter_stream(data)

    def token(self):
        try:
            return next(self.token_stream)
        except StopIteration:
            return None

    def test(self, data):
        self.input(data)
        while True:
            token = self.token()
            if not token:
                break
            print(token)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Takes python source code and performs lexical analysis')
    parser.add_argument('FILE', help="Input file with python source code")
    args = parser.parse_args()

    f = open(args.FILE, 'r')
    data = f.read()
    f.close()

    p = IndentLexer()
    p.test(data)
