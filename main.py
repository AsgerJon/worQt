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

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from worQt.app import AbstractApplication
from worQt.cad import CADApp
from yolo import yolo, runTests


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, AbstractApplication]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Entry point for cad larping project. Launches the CAD app and runs the
  Qt event loop until the window is closed (settings load on entry).
  """
  with CADApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  yolo(testMeBro, tester01)
