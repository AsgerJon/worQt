"""
Etc provides a descriptor to be owned by the running application providing
an absolute path to the 'etc' directory of the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import textFmt
from worktoy.work_io import validateExistingDirectory

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


def _etcPath() -> str:
  """Builds the absolute path to the 'etc.' directory."""

  here = os.path.dirname(os.path.abspath(__file__))
  src = os.path.join(here, '..', '..', )
  src = os.path.normpath(src)
  etc = os.path.join(src, 'etc', )
  return os.path.normpath(etc)


class Etc:
  """
  Etc provides a descriptor to be owned by the running application providing
  an absolute path to the 'etc' directory of the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __etc_path__ = _etcPath()

  #  Fallback Variables
  __fallback_sub_paths__ = ()

  #  Private Variables
  __field_owner__ = None
  __field_name__ = None
  __sub_paths__ = None

  #  Public Variables
  subPaths = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, ) -> None:
    subs = []
    for arg in args:
      if isinstance(arg, str):
        subs.append(arg)
    else:
      self.__sub_paths__ = (*subs,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @subPaths.GET
  def _getSubPaths(self, **kwargs) -> tuple[str, ...]:
    if self.__sub_paths__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__sub_paths__ = self.__fallback_sub_paths__
      return self._getSubPaths(_recursion=True)
    return self.__sub_paths__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: type, name: str, ) -> None:
    self.__field_owner__ = owner
    self.__field_name__ = name

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    out = os.path.join(self.__etc_path__, *self.subPaths)
    return validateExistingDirectory(out)

  def __repr__(self, ) -> str:
    infoSpec = """%s.%s = %s(%s)"""
    owner = self.__field_owner__.__name__
    fName = self.__field_name__
    name = type(self).__name__
    subs = ', '.join(repr(sp) for sp in self.subPaths) or ''
    info = infoSpec % (owner, fName, name, subs)
    return textFmt(info)

  def __str__(self, ) -> str:
    return os.path.join(self.__etc_path__, *self.subPaths)
