"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from icecream import ic

ic.configureOutput(includeContext=True)

from worQt.app import AbstractApplication, App
from yolo import yolo, runTests


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, AbstractApplication]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Testing that AbstractApplication does exist
  """
  with App(*sys.argv) as app:
    app.window.show()
  return 0


if __name__ == '__main__':
  yolo(tester01)
