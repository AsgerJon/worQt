"""
Base classes for tests of the 'worQt.layouts' package. 'LayoutCell' and
'LayoutIndex' are pure 'BaseObject' value types and test under a plain
'BaseTest'; 'GridLayout' and 'BaseLayout' are 'QObject's ('QGridLayout'),
so they test under 'AppTest' with a running 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class LayoutTest(BaseTest):
  """Base for the value-type ('LayoutCell'/'LayoutIndex') layout tests."""


class LayoutAppTest(AppTest):
  """Base for the 'QObject'-backed layout tests ('GridLayout')."""
