"""
SampleFile subclasses 'worQt.data.AbstractFile' and provides a file for
testing purposes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException

from tests import TempDir
from worQt.data import AbstractFile

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class SampleFile(AbstractFile):
  """
  SampleFile subclasses 'worQt.data.AbstractFile' and provides a file for
  testing purposes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_name__: str = 'sample.tmp'

  #  Private Variables
  __file_name__: Optional[str] = None

  #  Public Variables
  tempDir = TempDir()
  fileName: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createFileName(self, ) -> None:
    self.__file_name__ = self.__fallback_name__

  @fileName.GET
  def _getFileName(self, **kwargs) -> str:
    if self.__file_name__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createFileName()
      return self._getFileName(_recursion=True)
    if isinstance(self.__file_name__, str):
      return self.__file_name__
    raise TypeException('__file_name__', self.__file_name__, str)

  def _getFilePath(self, **kwargs) -> str:
    return str(os.path.join(self.tempDir.directory, self.fileName))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, fileName: str, **kwargs) -> None:
    self.__file_name__ = fileName

  @overload()
  def __init__(self, **kwargs) -> None:
    pass
