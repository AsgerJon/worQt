"""
The 'tests.test_phys' package contains tests for the 'worQt.phys'
package, the physics lab's own physics, which needs no Qt: plain
'BaseTest' classes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._phys_test import PhysTest, lShape

__all__ = (
  'PhysTest',
  'lShape',
)
