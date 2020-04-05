from .lexer import Lexer, LexicalError
from colorclass import Color


class Driver:
  """A class that orchestrates Expy.

      >>> driver = ExpyDriver(filename, source)
      >>> driver._lex() # compute the tokens
  """
  
  def __init__(self, filename, source):
    self.filename = filename
    self.source = source

  def _compute_linecol(self, position):
    """Compute line and column based on given position.
       Return: (line, column)"""
    workspace = self.source[:position]
    lines = workspace.split('\n') # XXX: this works, but optimize(?)
    column = len(lines[-1]) + 1
    return len(lines), column
    
  def _lex(self):
    """Pass the source to the lexical analyzer and
       handle lexical errors (if present). Return:
       a tuple of tokens"""
    try:
      lexer = Lexer(self.source)
      return *lexer.lex(),
    except LexicalError as error:
      line, column = self._compute_linecol(error.position)
      if (char := f'"{self.source[error.position]}"')[1] in '\n\0':
        char = 'end-of-input'
      print(Color('{autored}Lexical error{/autored}:\n'),
            error.message.capitalize(),
            f'near {char}',
            f'in {self.filename},',
            f'line {line}, column {column}.')
