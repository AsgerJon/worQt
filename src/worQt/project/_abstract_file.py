"""
Provides 'AbstractFile', a path-resolving gateway that runs caller-supplied
read or write callbacks against an open file handle.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
import os
from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.desc import AttriBox, Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.control_flow import SkipSet

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
    """
    Open 'self.filePath' for writing and call 'cb' with the open handle.

    'self.dirPath' is created if it does not already exist. 'cb' is
    responsible for what gets written; the handle is always closed
    afterwards. Note that 'dirPath' must be supplied by the subclass.

    Parameters
    ----------
    cb : Callable
        Called with the open write handle. Its return value is ignored.
    e : Callable, optional
        Open-error handler, called with the exception raised while opening
        the file. A truthy return swallows the error and 'save' returns;
        otherwise the exception is re-raised. When omitted, open errors
        always propagate.
    """
    os.makedirs(self.dirPath, exist_ok=True)
    e = maybe(e, lambda *_: False)
    f: Optional[IO] = None
    try:
      f = open(self.filePath, 'w')
    except Exception as exception:
      if e(exception):
        return
      raise exception
    else:
      cb(f)
    finally:
      if f is not None:
        f.close()

  def load(self, cb: Callable, e: Optional[Callable] = None) -> dict:
    """
    Open 'self.filePath' for reading and call 'cb' with the open handle.

    'cb' decides how the bytes are parsed; the handle is always closed
    afterwards.

    Parameters
    ----------
    cb : Callable
        Called with the open read handle. Its return value is returned by
        'load'.
    e : Callable, optional
        Open-error handler, called with the exception raised while opening
        the file. A truthy return swallows the error and 'load' returns an
        empty 'dict'; otherwise the exception is re-raised. When omitted,
        open errors always propagate.

    Returns
    -------
    object
        Whatever 'cb' returns, or an empty 'dict' if an open error was
        swallowed by 'e'.
    """
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
