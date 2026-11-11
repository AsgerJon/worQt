"""
The 'tests.test_engineering' package contains tests for the
'worQt.engineering' package: the structural model, which needs no Qt, in
plain 'BaseTest' classes, and its widgets in 'WidgetTest' classes, the
'run_*.py' / 'Run*' modules, running in a live 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._engineering_test import DEEP_BEAM, deepBeam
from ._engineering_test import EngineeringTest, EngineeringWidgetTest

__all__ = (
  'DEEP_BEAM',
  'deepBeam',
  'EngineeringTest',
  'EngineeringWidgetTest',
)
