"""
The 'tests.test_space' package contains tests for the
'worQt.gaming.space' package, run without a window: plain 'BaseTest'
classes, the flight's kernel on the CPU.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._space_test import FRAME, SpaceTest

__all__ = (
  'FRAME',
  'SpaceTest',
)
