"""
The 'testMeBro' function runs the full test suite!
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTestSuite


def testMeBro() -> int:
  """
  Run the full test suite. This is a sanity check that the test suite runs
  at all, and that it passes on the current codebase.
  """
  return AppTestSuite().runAll()
