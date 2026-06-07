"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from worQt.app import AbstractApplication
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  pass


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, AbstractApplication]
  for item in stuff:
    print(item)
  return 0


if __name__ == '__main__':
  yolo(testMeBro, )
