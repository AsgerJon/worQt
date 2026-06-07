"""
DataTest subclasses 'BaseTest' from the 'worktoy.work_test' package and
the base class for tests of the 'worQt.data' package.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from tests import TempDir

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias


class DataTest(BaseTest):
  """
  DataTest subclasses 'BaseTest' from the 'worktoy.work_test' package and
  the base class for tests of the 'worQt.data' package.
  """

  @classmethod
  def setUpClass(cls) -> None:
    """
    Set up the test class.
    """
    super().setUpClass()
    cls.tempDir = TempDir()

  def setUp(self, ) -> None:
    """
    Set up the test.
    """
    super().setUp()
    self.tempDir.clear()

  def tearDown(self, ) -> None:
    """
    Tear down the test.
    """
    self.tempDir.clear()
    super().tearDown()
