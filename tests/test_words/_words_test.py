"""
WordsTest subclasses 'BaseTest' from the 'worktoy.work_test' package and is
the base class for tests of the 'worQt.words' package. It provides a cleared
temporary directory (the shared 'tests/_scratch') around each test.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from tests import TempDir

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class WordsTest(BaseTest):
  """Base test for the 'worQt.words' package, with a cleared temp dir."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.tempDir = TempDir()

  def setUp(self, ) -> None:
    super().setUp()
    self.tempDir.clear()

  def tearDown(self, ) -> None:
    self.tempDir.clear()
    super().tearDown()
