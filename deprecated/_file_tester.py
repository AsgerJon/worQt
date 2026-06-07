"""
FileTester subclasses 'AbstractFile' from 'worQt.data' and provides a
subclass for testing purposes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import FixBox, AttriBox

from tests import TempDir
from worQt.data import AbstractFile

if TYPE_CHECKING:  # pragma: no cover
  pass


class FileTester(AbstractFile):
  """
  FileTester subclasses 'AbstractFile' from 'worQt.data' and provides a
  subclass for testing purposes.
  """

  tempDir = FixBox[TempDir]()
  fileName = AttriBox[str]()

  def clear(self) -> None:
    self.tempDir.clear()
