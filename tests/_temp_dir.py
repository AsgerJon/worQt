"""
TempDir subclasses 'BaseObject' from 'worktoy.mcls' and provides a
temporary directory in the 'tests' module.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject, BaseMeta

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias

_HERE: str = os.path.dirname(os.path.abspath(__file__))
_TEMP_DIR: str = os.path.join(_HERE, '_scratch')


class _MetaDir(BaseMeta):
  __temp_dir__: str = _TEMP_DIR
  directory: Field[str] = Field()

  @directory.GET
  def _getDirectory(cls, ) -> str:
    return cls.__temp_dir__


class TempDir(BaseObject, metaclass=_MetaDir):
  """
  TempDir subclasses 'BaseObject' from 'worktoy.mcls' and provides a
  temporary directory in the 'tests' module.
  """

  directory: str = Field()

  @classmethod
  def _classGetDirectory(cls: _MetaDir, ) -> str:
    mcls = type(cls)
    field = mcls.directory
    return field.__get__(cls, mcls, )

  @directory.GET  # noqa
  def _getDirectory(self, ) -> str:
    return self._classGetDirectory()

  @classmethod
  def _clearDirectory(cls, directory: str) -> None:
    if not os.path.exists(directory):
      raise FileNotFoundError
    if os.path.isfile(directory):
      raise NotADirectoryError
    for item in os.listdir(directory):
      itemPath: str = os.path.join(directory, item)
      if os.path.isfile(itemPath):
        os.remove(itemPath)
      else:
        cls._clearDirectory(itemPath)
        os.rmdir(itemPath)

  @classmethod
  def clear(cls, ) -> None:
    cls._clearDirectory(cls._classGetDirectory())
