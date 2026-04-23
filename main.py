"""Main Tester Script"""
#  AGPL-3.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from string import ascii_letters

from PySide6.QtWidgets import QMainWindow
from pyperclip import copy
from worktoy.utilities import textFmt

from worQt.app import App
from worQt.windows import MainWindow
from yolo import yolo, runTests


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Testing traditional QApplication entry points using a simple QMainWindow
  instance as the main application window.
  """
  with App(MainWindow, 'worQt') as app:
    QMainWindow.setWindowIcon(app.window, app.appIcon)
    app.window.update()
    app.window.show()
    app.window.setMinimumSize(640, 640)
  return int(app)


def tester02(*args, ) -> int:
  """
  Testing str.capitalize
  """
  testStrings = (
    """never gonna give you up""",
    """NEVER GONNA LET YOU DOWN""",
    )
  for s in testStrings:
    print(48 * '_')
    print(s)
    print(str.capitalize(s))
    print(48 * '¨')
  return 0


def tester03() -> int:
  """
  breh
  """
  lol = """
  
  Social Democrats	779,252	21.84	38	–12
Green Left	413,306	11.58	20	+5
Venstre	361,689	10.14	18	–5
Liberal Alliance	334,421	9.37	16	+2
Danish People's Party	324,518	9.10	16	+11
Moderates	274,775	7.70	14	–2
Conservative People's Party	270,749	7.59	13	+3
Red–Green Alliance	226,037	6.34	11	+2
Danish Social Liberal Party	207,442	5.81	10	+3
Denmark Democrats	205,302	5.75	10	–4
The Alternative	91,770	2.57	5	–1
Citizens' Party	75,928	2.13	4	+4
Independents	2,436	0.07	0	0
Total	3,567,625	100.00	175	
  """
  lines = str.splitlines(lol)
  dataLines = []
  for line in lines:
    line = str.strip(line)
    try:
      mandateCount = int(str.strip(str.split(line)[-2]))
    except (IndexError, ValueError):
      continue
    partyName = [c for c in line if c in """%s """ % ascii_letters]
    dataLine = """%s: %20d""" % (''.join(partyName).strip(), mandateCount)
    dataLines.append(textFmt(dataLine))
  data = '\n'.join(dataLines)
  copy(data)
  print(data)
  return 0


def tester04() -> int:
  """ breh"""
  print(1 / float('inf'))
  print(-1 / float('inf'))
  return 0


def tester05() -> int:
  """ breh"""


if __name__ == '__main__':
  # yolo(tester04)
  yolo(runTests, tester01)
