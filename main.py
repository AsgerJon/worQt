"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QMainWindow

from worQt.app import Main
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
  """MainWindow test"""
  for item in dir(os):
    print(item)
    break
  for item in dir(os):
    if 'exec' in item:
      print(help(getattr(os, item)))
  return 0


if __name__ == '__main__':
  yolo(runTests, tester01)
