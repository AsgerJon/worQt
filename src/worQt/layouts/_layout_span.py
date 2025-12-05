"""
LayoutSpan encapsulates the span of a widget in a grid layout.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import textFmt, maybe

from moreworktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Type, TypeAlias, Callable, Iterator


class LayoutSpan(BaseObject):
  """
  LayoutSpan encapsulates the span of a widget in a grid layout.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __row_keys__ = ('row', 'rows', 'r', 'x', '0',)
  __col_keys__ = ('col', 'cols', 'c', 'y', '1',)

  #  Fallback Variables
  __fallback_rows__ = 1
  __fallback_cols__ = 1

  #  Private Variables
  __row_span__ = None
  __col_span__ = None

  #  Public Variables
  rows = Field()
  cols = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @rows.GET
  def _getRows(self, **kwargs) -> int:
    if self.__row_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__row_span__ = self.__fallback_rows__
      return self._getRows(_recursion=True)
    return self.__row_span__

  @cols.GET
  def _getCols(self, **kwargs) -> int:
    if self.__col_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__col_span__ = self.__fallback_cols__
      return self._getCols(_recursion=True)
    return self.__col_span__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[int]:
    yield self.rows
    yield self.cols

  def __len__(self, ) -> int:
    return 2

  def __abs__(self, ) -> int:
    return self.rows * self.cols

  def __bool__(self, ) -> bool:
    return True if self.rows and self.cols else False

  def __getitem__(self, identifier: Any) -> int:
    raise NotImplementedError

  def __eq__(self, other: Any) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self.rows != other.rows:
      return False
    if self.cols != other.cols:
      return False
    return True

  def __hash__(self, ) -> int:
    return hash((self.rows, self.cols))

  def __str__(self, ) -> str:
    infoSpec = """%s spanning %d rows and %d columns."""
    info = infoSpec % (type(self).__name__, self.rows, self.cols,)
    return textFmt(info)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d)"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, self.row, self.col,)
    return textFmt(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveIndex(self, index: int) -> int:
    if index > 1:
      raise IndexError
    if index < 0:
      return self._resolveIndex(index + len(self))
    return self.cols if index % 2 else self.rows

  def _resolveKey(self, key: str) -> int:
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, *args, **kwargs) -> None:
    self.__row_span__, self.__col_span__ = args
    if kwargs:
      self.__init__(**kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.__row_span__ = other.__row_span__
    self.__col_span__ = other.__col_span__
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    for key, val in kwargs.items():
      if key.lower() in self.__row_keys__:
        self.__row_span__ = val
      if key.lower() in self.__col_keys__:
        self.__col_span__ = val
    self.__row_span__ = maybe(self.__row_span__, 1)
    self.__col_span__ = maybe(self.__col_span__, 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
