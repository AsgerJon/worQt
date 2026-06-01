"""
AppTest subclasses 'BaseTest' from 'worktoy.work_test' and provides the
base class for the tests in 'tests.test_app'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

if TYPE_CHECKING:  # pragma: no cover
  pass


class AppTest(BaseTest):
  """Base class for tests in 'tests.test_app'."""
