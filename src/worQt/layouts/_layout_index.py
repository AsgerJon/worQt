"""
LayoutIndex specifies the placement of a widget in a 'WidgetLayout' object.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

from moreworktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator, Union


class LayoutIndex(BaseObject):
  """
  LayoutIndex specifies the placement of a widget in a 'WidgetLayout' object.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __row_keys__ = ('row', 'r', 'x', '0',)
  __col_keys__ = ('col', 'c', 'y', '1',)

  #  Fallback Variables
  __fallback_row__ = 0
  __fallback_col__ = 0

  #  Private Variables
  __row_pos__ = None
  __col_pos__ = None

  #  Public Variables
  row = Field()
  col = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @row.GET
  def _getRow(self, **kwargs) -> int:
    if self.__row_pos__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__row_pos__ = self.__fallback_row__
      return self._getRow(_recursion=True)
    return self.__row_pos__

  @col.GET
  def _getCol(self, **kwargs) -> int:
    if self.__col_pos__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__col_pos__ = self.__fallback_col__
      return self._getCol(_recursion=True)
    return self.__col_pos__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveIndex(self, index: int) -> int:
    if index >= len(self):
      infoSpec = """Index '%d' out of range for '%s' object with length 
      '%d'."""
      clsName = type(self).__name__
      info = infoSpec % (index, clsName, len(self),)
      raise IndexError(textFmt(info))
    if index < 0:
      return self._resolveIndex(index + len(self))
    return [*self, ][index]

  def _resolveKey(self, key: str) -> int:
    if key.lower() in self.__row_keys__:
      return self.row
    if key.lower() in self.__col_keys__:
      return self.col
    raise KeyError(key)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[int]:
    yield self.row
    yield self.col
    yield self.rowSpan
    yield self.colSpan

  def __len__(self, ) -> int:
    return 4

  def __abs__(self, ) -> int:
    return abs(self.span)

  def __eq__(self, other: Any) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self.row != other.row:
      return False
    if self.col != other.col:
      return False
    if self.rowSpan != other.rowSpan:
      return False
    if self.colSpan != other.colSpan:
      return False
    return True

  def __hash__(self, ) -> int:
    return hash((self.rows, self.cols, hash(self.span)))

  def __getitem__(self, identifier: Any) -> int:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, int, str)

  def __str__(self, ) -> str:
    infoSpec = """LayoutIndex at row: %d and column: %d."""
    info = infoSpec % (self.row, self.col,)
    return textFmt(info)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d)"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, self.row, self.col,)
    return textFmt(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, row: int, col: int, **kwargs, ) -> None:
    self.__row_pos__ = row
    self.__col_pos__ = col
    if kwargs:
      self.__init__(**kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs, ) -> None:
    self.__row_pos__ = other.row
    self.__col_pos__ = other.col
    if kwargs:
      self.__init__(**kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    for key, val in kwargs.items():
      if key.lower() in self.__row_keys__:
        self.__row_pos__ = val
      if key.lower() in self.__col_keys__:
        self.__col_pos__ = val
