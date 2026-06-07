"""
Provides 'AbstractFile', a path-resolving gateway that runs caller-supplied
read or write callbacks against an open file handle.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
import os
from typing import TYPE_CHECKING, TypeVar

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, IO

T = TypeVar('T')


class AbstractFile(BaseObject):
  """
  Runs a caller-supplied callback against an open handle to a file, owning
  the open and close.

  Where the file lives is left to the subclass through the abstract
  'filePath' getter; what goes into the file is the caller's concern.

  Attributes
  ----------
  filePath : str
      The absolute path of the file. The getter is abstract - subclasses
      must implement it.

  Methods
  -------
  save(cb, e=None)
      Open 'filePath' for writing and pass the handle to 'cb'.
  load(cb, e=None)
      Open 'filePath' for reading, pass the handle to 'cb' and return its
      result.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  filePath: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @filePath.GET
  def _getFilePath(self, **kwargs) -> str:
    """
    Subclasses must implement this method to define their file path.
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def save(self, cb: Callable, e: Optional[Callable] = None) -> None:
    e = maybe(e, lambda *_: False)
    targetPath = self.filePath
    os.makedirs(os.path.dirname(targetPath), exist_ok=True)
    tmpPath = '%s.tmp' % (targetPath,)  # same dir = same fs = atomic
    try:
      f: IO = open(tmpPath, 'w')
    except Exception as exception:
      if e(exception):
        return
      raise exception
    try:
      with f:
        cb(f)
      os.replace(tmpPath, targetPath)
    except BaseException:
      if os.path.exists(tmpPath):
        os.remove(tmpPath)
      raise

  def load(self, cb: Callable, e: Optional[Callable] = None) -> dict:
    e = maybe(e, lambda *_: False)
    f: Optional[IO] = None
    try:
      f = open(self.filePath, 'r')
    except Exception as exception:
      if e(exception):
        return dict()
      raise exception
    else:
      return cb(f)
    finally:
      if f is not None:
        f.close()
