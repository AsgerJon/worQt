"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2025 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from PySide6.QtCore import QObject
import shiboken6
from PySide6.QtGui import QPixmap, QPaintDevice, QIcon
from PySide6.QtWidgets import QWidget

from main_cls import Breh
from worQt import getEtc, getIconPath
from worQt.app import App
from worQt.tools.geometry import Size
from yolo import yolo, runTests

sys.path.append('./src')
sys.path.append('./src/worktoy')


def tester00() -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset]
  for item in stuff:
    print(item)
  return 0


def tester01() -> int:
  """Shiboken"""
  entries = []

  for (key, val) in QWidget.__dict__.items():
    entries.append((key, type(val).__name__))

  n = max([len(entry[0]) for entry in entries])

  infoSpec = """%%%ds of type %%s""" % (n,)

  for entry in entries:
    key, val = entry
    print(infoSpec % (key, val))

  return 0


def tester02() -> int:
  """Testing module file stuff"""
  print(Breh.__module__)
  print(App.__module__)
  brehModule = sys.modules.get(Breh.__module__)
  print(brehModule.__file__)
  return 0


def tester03() -> int:
  """Testing mro of QPixmap"""
  cls = QIcon
  c = 10
  print(cls.__name__)
  print(cls.__bases__)
  return 0


def tester04() -> int:
  """Testing etc"""
  print(getIconPath())
  return 0


def tester05() -> int:
  """Testing size fitting"""
  big = Size(160, 100)
  small = Size(120, 90)
  fitted = small.fit(big)
  print(small.fit(big), big)
  print(big.fit(small), small)

  return 0


if __name__ == '__main__':
  yolo(runTests, tester00)
