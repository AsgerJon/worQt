"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)
#  The test windows main.py runs open without taking the focus (user,
#  2026-11-15: "do something so the window doesn't grab focus pls"):
#  shown unactivated, never focused; the children inherit it. Set it to
#  '0' to have them raised and activated.
os.environ.setdefault('QTEST_NO_FOCUS', '1')

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from yolo import yolo, runTests


def tester00() -> int:
  """
  Hello World!
  """
  stuff = [os, sys, ]
  for item in stuff:
    print(item)
  return 0


if __name__ == '__main__':
  yolo(tester00)
