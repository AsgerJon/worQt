"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from yolo import yolo, runTests

from PySide6.QtCore import Qt
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from worQt.app import Main
from worQt.windows import MainWindow


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


if __name__ == '__main__':
  yolo(runTests, tester01)
