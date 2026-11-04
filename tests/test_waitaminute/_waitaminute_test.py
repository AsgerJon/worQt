"""
WaitTest is the base for tests of the 'worQt.waitaminute' package. The
event exceptions carry Qt event/widget/painter objects, so the tests build
those against a running 'QApplication' under 'AppTest'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class WaitTest(AppTest):
  """Base for the 'worQt.waitaminute' event-exception tests."""
