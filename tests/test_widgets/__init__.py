"""
The 'tests.test_widgets' package contains tests for the 'worQt.widgets'
package. These run as 'AppTest' classes (a live 'QApplication' in a child
process), hence the 'run_*.py' / 'Run*' naming the 'worQt.qtest' runner
discovers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._widget_test import WidgetTest

__all__ = (
  'WidgetTest',
)
