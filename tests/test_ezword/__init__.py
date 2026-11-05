"""
The 'tests.test_ezword' package contains tests for the 'worQt.ezword'
package: the text model in plain 'BaseTest' classes, and the EZWord GUI
in 'WidgetTest' classes, the 'run_*.py' / 'Run*' modules, running in a
live 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._ezword_test import EZWordTest, EZWordWidgetTest
from ._ezword_test import QuietEZWordApp, QuietEZWordWindow

__all__ = (
  'EZWordTest',
  'EZWordWidgetTest',
  'QuietEZWordApp',
  'QuietEZWordWindow',
)
