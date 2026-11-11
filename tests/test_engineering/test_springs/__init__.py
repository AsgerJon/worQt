"""
The 'tests.test_engineering.test_springs' package contains tests for the
'worQt.engineering.springs' package, masses on springs and dampers
swinging in space: the model, which needs no Qt, in plain 'BaseTest'
classes; the app's widgets in 'WidgetTest' classes, the 'run_*.py' /
'Run*' modules.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._springs_test import hanging, chain
from ._springs_test import SpringsTest, SpringsWidgetTest

__all__ = (
  'hanging',
  'chain',
  'SpringsTest',
  'SpringsWidgetTest',
)
