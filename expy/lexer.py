try:
  import re2 as re
except ImportError:
  import re

from collections import namedtuple


class LexicalError(Exception):

  def __init__(self, position, message):
    self.position = position
    self.message = message


Match = namedtuple('ExpyMatch', 'value pos')


class Token:

  def __init__(self, type_, value, pos):
    self.type = type_
    self.value = value
    self.pos = pos

  def __eq__(self, value):
    return self.type == value.type

  def __ne__(self, value):
    return not self.__eq__(value)

  def __repr__(self):
    return f'Token(type={self.type}, value="{self.value}", pos={self.pos})'


class Lexer:

  KEYWORDS = {
    'not', 'or', 'and', 'of', 'in', 'is',
    # TODO
  }

  SPECIALS = {
    '+', '-', '*', '/', '=',
    # TODO
  }

  def __init__(self, source):
    self.source = source
    self.indent = [0]
    self.pos = 0
  
  def _lexical_error(self, message, position=None):
    raise LexicalError(position if position is not None else self.pos, message)

  def _match(self, pattern, group = 0):
    if match := re.match(pattern, self.source[(start := self.pos):]):
      value = match.group(group)
      self.pos += len(value)
      return Match(value, start)
    return False

  def _check(self, pattern):
    return bool(re.match(pattern, self.source[self.pos]))

  def _next(self):
    """Grab the following token."""
    if self.pos >= len(self.source):
      return False
    elif self._match(r'"[^\n]+'):
      return self._next() # XXX: ignore comment.
    elif m := self._match(r'[a-zA-Z_][a-zA-Z0-9_]*'):
      if m.value in self.KEYWORDS:
        return m.value.upper(), m.value, m.pos
      return 'CLASSNAME' if m.value[0].isupper() else 'IDENTIFIER', m.value, m.pos
    elif m := self._match(r'[0-9]+j'):
      return 'IMAG', m.value, m.pos
    elif m := self._match(r'0x'):
      if t := self._match(r'[A-Fa-f0-9]+'):
        return 'HEX', t.value, m.pos
      self._lexical_error('bad number: "0x"')
    elif m := self._match(r'0o'):
      if t := self._match(r'[0-7]+'):
        return 'OCT', t.value, m.pos
      self._lexical_error('bad number: "0o"')
    elif m := self._match(r'0b'):
      if t := self._match(r'[01]+'):
        return 'BIN', t.value, m.pos
      self._lexical_error('bad number: "0b"')
    elif m := self._match(r'[0-9]+\.[0-9]+(e-?[0-9]+)?'):
      return 'FLOAT', m.value, m.pos
    elif m := self._match(r'[1-9][0-9]*|0'):
      return 'DEC', m.value, m.pos
    elif m := self._match(r'\''):
      def compute_string():
        while True:
          if self._match(r'\n|\x00'):
            self._lexical_error('bad string', m.pos)
          elif self._match(r'\''):
            break
          elif self._match(r'\\'):
            if esc := self._match(r'[nrtv0\'"\\]'):
              yield '\\' + esc.value
            else:
              self._lexical_error('bad escape sequence')
          else:
            yield (self._match('.') or self._lexical_error('bad string', m.pos - 1)).value
      return 'STR', ''.join(compute_string()), m.pos
    elif m := self._match('(\n\r?)+'):
      def compute_indent():
        if (t := self._match(r'[ \t]*')) and self._check(r'[^"\n]+'):
          level = len(t.value)
          if level > self.indent[-1]:
            self.indent.append(level)
            yield 'INDENT', None, m.pos
          elif level not in self.indent:
            self._lexical_error('inconsistent indentation')
          elif level < self.indent[-1]:
            while self.indent[-1] > level:
              self.indent.pop()
              yield 'DEDENT', None, m.pos
      return '__MANY', ('NEWLINE', None, m.pos), *(compute_indent() or ())
    elif m := self._match('|'.join(re.escape(special) for special in (self.SPECIALS))):
      return m.value, m.value, m.pos
    elif m := self._match('\x00'):
      return 'EOF', None, m.pos
    elif self._match('[ \t\r]+'):
      return self._next()
    else:
      self._lexical_error('bad lexeme')
  
  def lex(self):
    while token := self._next():
      if token[0] == '__MANY':
        for entry in token[1:]:
          yield Token(*entry)
      else:
        yield Token(*token)
