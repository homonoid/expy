from .driver import Driver
import sys
import readline


if len(sys.argv[1:]) == 1:
  with open(sys.argv[1]) as file:
    source = file.read() + '\n\0'
    driver = Driver(f'"{file.name}"', source)
    if tokens := driver._lex():
      print(*tokens, sep='\n')
elif len(sys.argv[1:]) > 1:
  print('usage: python -m expy [file.expy]')
else:
  while True:
    line = input('> ') + '\n\0'
    driver = Driver('<stdin>', line)
    if tokens := driver._lex():
      print(*tokens, sep='\n')
