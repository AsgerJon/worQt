"""
The 'tests.test_qtest' package contains tests for the 'worQt.qtest' test
harness itself: discovery, the per-class runner, the namespace/metaclass
that collect test methods, and the suite that ties them together.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._qtest_test import QTestTest

__all__ = (
  'QTestTest',
)
