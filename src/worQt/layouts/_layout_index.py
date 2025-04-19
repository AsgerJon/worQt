"""LayoutIndex provides a hashable index for a position in the layout. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field
from worktoy.mcls import BaseObject
from worktoy.static import overload, THIS
from worktoy.text import typeMsg
from worktoy.waitaminute import MissingVariable

from moreworktoy.waitaminute import WriteOnceError

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Self


class LayoutIndex(BaseObject):
  """This data class provides a hashable index for a position in the
  widget. It has fields:
  - col: int -> Column index indicating the number of columns to the left
  - row: int -> Row index indicating the number of rows above"""

  __iter_contents__ = None

  __n_cols__ = None
  __n_rows__ = None

  col = Field()  # Column index indicating the number of columns to the left
  row = Field()  # Row index indicating the number of rows above

  @col.GET
  def _getCol(self) -> int:
    """Returns the column index. """
    if self.__n_cols__ is None:
      raise MissingVariable('__n_cols__', int)
    if isinstance(self.__n_cols__, int):
      return self.__n_cols__
    raise TypeError(typeMsg('__n_cols__', self.__n_cols__, int))

  @row.GET
  def _getRow(self) -> int:
    """Returns the row index. """
    if self.__n_rows__ is None:
      raise MissingVariable('__n_rows__', int)
    if isinstance(self.__n_rows__, int):
      return self.__n_rows__
    raise TypeError(typeMsg('__n_rows__', self.__n_rows__, int))

  @col.SET
  def _setCol(self, value: int) -> None:
    """Sets the column index. """
    if self.__n_cols__ is not None:
      raise WriteOnceError('__n_cols__', self.__n_cols__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__n_cols__', value, int))
    self.__n_cols__ = value

  @row.SET
  def _setRow(self, value: int) -> None:
    """Sets the row index. """
    if self.__n_rows__ is not None:
      raise WriteOnceError('__n_rows__', self.__n_rows__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__n_rows__', value, int))
    self.__n_rows__ = value

  def __hash__(self, ) -> int:
    """Returns the hash of the index. """
    return hash((self.col, self.row))

  def __eq__(self, other: Self) -> bool:
    """Returns True if the index is equal to the other index. """
    if self.col == other.col and self.row == other.row:
      return True
    return False

  def __str__(self) -> str:
    """Returns the string representation of the index. """
    infoSpec = """%s[row=%d, col=%d]"""
    name = type(self).__name__
    return infoSpec % (name, self.row, self.col)

  def __repr__(self) -> str:
    """Returns the string representation of the index. """
    infoSpec = """%s(row=%d, col=%d)"""
    name = type(self).__name__
    return infoSpec % (name, self.row, self.col)

  def __iter__(self) -> Self:
    """Returns an iterator for the index. """
    self.__iter_contents__ = [self.row, self.col]
    return self

  def __bool__(self) -> bool:
    """Returns True if the index is not empty. """
    return True if self.row or self.col else False

  def __next__(self) -> Any:
    """Returns the next item in the iterator. """
    try:
      return self.__iter_contents__.pop(0)
    except IndexError:
      raise StopIteration
    finally:
      if not self.__iter_contents__:
        self.__iter_contents__ = None

  @overload(int, int)
  def __init__(self, row: int, col: int) -> None:
    """Initializes the index with the given row and column. """
    self.__n_rows__ = row
    self.__n_cols__ = col

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    """Initializes the index with the given index. """
    self.__n_rows__ = other.row
    self.__n_cols__ = other.col

  @overload(tuple)
  @overload(list)
  def __init__(self, other: tuple | list) -> None:
    """Initializes the index with the given index. """
    if len(other) != 2:
      raise ValueError('Index must be a tuple or list of length 2.')
    if not isinstance(other[0], int):
      raise TypeError(typeMsg('row', other[0], int))
    if not isinstance(other[1], int):
      raise TypeError(typeMsg('col', other[1], int))
    self.__n_rows__ = other[0]
    self.__n_cols__ = other[1]

  @overload(int)
  def __init__(self, index: int) -> None:
    """Initializes the index with the given index. """
    self.__n_rows__ = index
    self.__n_cols__ = index

  @overload()
  def __init__(self, **kwargs) -> None:
    """Initializes the index with the default values. """
    self.__n_rows__ = kwargs.get('row', 0)
    self.__n_cols__ = kwargs.get('col', 0)
