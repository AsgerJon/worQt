"""
DocumentTest subclasses 'BaseTest' from 'worktoy.work_test' and is the base
class for tests of the 'worQt.document' package. 'document' is Qt-free, so
these run in-process; the only fixture is a temporary directory for the
save/load round-trips.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from tests import TempDir

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class DocumentTest(BaseTest):
  """Base for 'worQt.document' tests: a cleared temp directory per test."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.tempDir = TempDir()
    os.makedirs(cls.tempDir.directory, exist_ok=True)

  def setUp(self, ) -> None:
    super().setUp()
    self.tempDir.clear()

  def tearDown(self, ) -> None:
    self.tempDir.clear()
    super().tearDown()

  def path(self, name: str = 'fem.json') -> str:
    """An absolute path inside the per-test temp directory."""
    return os.path.join(self.tempDir.directory, name)
