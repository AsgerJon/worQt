"""
The 'testMeBro' function runs the full test suite!
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import AppTestSuite


def testMeBro() -> int:
  """
  The 'testMeBro' function runs the full test suite and returns 0 when it
  passed, 1 otherwise.
  """
  return AppTestSuite().runAll()
