"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from PySide6.QtCore import Qt
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from worQt.app import Main
from worQt.geometry import Rect
from worQt.nums import MouseButtonNum
from worQt.windows import MainWindow
from yolo import yolo, runTests


def tester00() -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset]
  for item in stuff:
    print(item)
  return 0


def tester01() -> int:
  """App test"""
  with Main[MainWindow](*sys.argv) as main:
    print('_' * 77)
    print("""Entered main context. """)
    main.windowInstance.show()
    print("""Opened main window.""")
    print('¨' * 77)
  return 0


def tester02() -> int:
  """Testing MouseButtonNum"""
  for item in MouseButtonNum:
    print(item, 'truthy: %s' % 'True' if item else 'False')
  print("""MouseButtonNum(Qt.MouseButton.LeftButton)""", end=' ')
  print(MouseButtonNum(Qt.MouseButton.LeftButton))

  infoSpec = """Qt.MouseButton.NoButton truthy: %s"""
  flag = 'True' if Qt.MouseButton.NoButton else 'False'
  info = infoSpec % flag
  print(info)

  return 0


def tester03() -> int:
  """Testing error message when __slots__ class tries to set dynamically"""

  class Foo:
    __slots__ = ('bar',)

  foo = Foo()

  try:
    setattr(foo, 'breh', 69)
  except Exception as exception:
    infoSpec = """Caught %s: %s"""
    excType = type(exception).__name__
    info = infoSpec % (excType, str(exception))
    print(info)
    return 0
  else:
    print("""Expected an exception lmao""")
    return 1


def tester04() -> int:
  """Testing error when calling overloaded method with arguments of
  unsupported type signature. """

  class Foo(BaseObject):
    """Class with overloaded method."""

    x = AttriBox[int]()
    y = AttriBox[int]()

    @overload(int, int)
    def __init__(self, x: int, y: int) -> None:
      """Constructor with two integers."""
      self.x = x
      self.y = y

    @overload(str, str)
    def __init__(self, x: str, y: str) -> None:
      self.__init__(int(x), int(y))

  try:
    foo = Foo()
  except Exception as exception:
    infoSpec = """Caught %s: %s"""
    excType = type(exception).__name__
    info = infoSpec % (excType, str(exception))
    print(info)
    return 0
  else:
    print("""Expected an exception lmao""")
    return 1

  return 0


if __name__ == '__main__':
  yolo(runTests, tester01)
