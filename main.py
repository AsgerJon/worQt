"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import configparser
import enum
import os
import sys

from PySide6.QtCore import QEvent

from worQt.app import Main
from worQt.desQt import Settings
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
  """Testing enum.IntEnum"""

  for key, value in enum.IntEnum.__dict__.items():
    print(key, type(value))
  for key, value in enum.Enum.__dict__.items():
    print(key, type(value))
  return 0


def tester03() -> int:
  """Testing configparser"""

  class Foo:
    bar = Settings('example')

  for item in Foo().bar:
    print(item)
  infoSpec = """%40s : %37s"""
  keyHeader = str.rjust('Key', 40)
  valueHeader = str.ljust('Value', 37)
  info = infoSpec % (keyHeader, valueHeader)
  print('-' * len(info))
  print(info)
  for key, value in Foo().bar.items():
    keyStr = str.rjust('%s <%s>' % (key, type(value).__name__), 40)
    valueStr = str(value)
    if len(valueStr) > 37:
      valueStr = '%s...' % valueStr[:34]
    valueStr = str.ljust(valueStr, 37)
    info = infoSpec % (keyStr, valueStr)
    print(info)
  print('-' * len(info))

  return 0


if __name__ == '__main__':
  yolo(runTests, tester01)
