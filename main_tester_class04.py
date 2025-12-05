"""
Testing __init__ in multiple inheritance scenario.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.utilities import textFmt

base = type('Base', (object,), dict())

left = type('Left', (base,), dict())
right = type('Right', (base,), dict())

leftRight = type('LeftRight', (left, right), dict())
rightLeft = type('RightLeft', (right, left), dict())

Sus = type('_place_holder__', (object,), dict())

try:

  class Sus(leftRight, rightLeft):
    pass
except Exception as exception:
  infoSpec = """Caught '%s'!: '%s'"""
  excType = type(exception).__name__
  excMsg = str(exception)
  info = textFmt(infoSpec % (excType, excMsg))
  print(info)
else:
  infoSpec = """Successfully created class: '%s'!"""
  className = Sus.__name__
  info = textFmt(infoSpec % className)
  print(info)
finally:
  print("""lol""")
