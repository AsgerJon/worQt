"""
The 'tests.test_vidget' package contains tests for the 'worQt.vidget'
package. Each 'Run*' class subclasses 'VidgetTest', a 'WidgetTest' with
the gestures Vi needs, running in a live 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._vidget_test import VidgetTest

__all__ = (
  'VidgetTest',
)
