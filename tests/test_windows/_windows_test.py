"""
Base classes for tests of the 'worQt.windows' package. The declarative
menu *registration* is class-level (descriptors register their types at
import), so it tests under a plain 'BaseTest'; building the menus, bar and
actions constructs 'QObject's, so that tests under 'AppTest' with a running
'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class WindowsTest(BaseTest):
  """Base for the class-level (registration) windows tests."""


class WindowsAppTest(AppTest):
  """Base for the 'QObject'-backed windows tests (menus, bar, actions)."""
