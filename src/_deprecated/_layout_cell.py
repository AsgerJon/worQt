"""
LayoutCell encapsulates a single cell in a grid layout.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt, stringList
from worktoy.waitaminute import TypeException, WriteOnceError

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Self, Iterator


class LayoutCell(BaseObject):
  """
  LayoutCell encapsulates a single cell in a grid layout.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __row_keys__ = stringList("""row, r, y, line, vertical,""", )
  __col_keys__ = stringList("""col, c, x, column, horizontal""")

  #  Fallback Variables
  __fallback_col__ = 0
  __fallback_row__ = 0

  #  Private Variables
  __col_id__ = None
  __row_id__ = None

  #  Public Variables
  col = Field()
  row = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @col.GET
  def _getCol(self, **kwargs) -> int:
    if self.__col_id__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__col_id__ = self.__fallback_col__
      return self._getCol(_recursion=True, )
    if isinstance(self.__col_id__, int):
      return self.__col_id__
    raise TypeException('__col_id__', self.__col_id__, int, )

  @row.GET
  def _getRow(self, **kwargs) -> int:
    if self.__row_id__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__row_id__ = self.__fallback_row__
      return self._getRow(_recursion=True, )
    if isinstance(self.__row_id__, int):
      return self.__row_id__
    raise TypeException('__row_id__', self.__row_id__, int, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __setattr__(self, key: str, value: Any) -> None:
    """Implementing immutability for the column and row identifiers."""
    if key in ['__col_id__', '__row_id__', ]:
      existing = object.__getattribute__(self, key)
      if existing is not None:
        raise WriteOnceError(getattr(type(self), key), existing, value, )
    object.__setattr__(self, key, value)

  def _resolveOther(self, other: Any) -> Self:
    """
    Resolves the 'other' operand into another instance of the present
    class. Subclasses need not override this method as it resolves to the
    class of the 'self' operand. It centralizes the logic for resolving
    the other operand in binary methods.
    """
    cls = type(self)
    if isinstance(other, cls):
      return other
    try:
      out = cls(other)
    except (ValueError, TypeError):
      return NotImplemented
    else:
      return out

  def __eq__(self, other: Any) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self.row != other.row:
      return False
    if self.col != other.col:
      return False
    return True

  def __ne__(self, other: Any) -> bool:
    if self.__eq__(other) is NotImplemented:
      return NotImplemented
    return False if self == other else True

  def __len__(self, ) -> int:
    return 2

  def __bool__(self, ) -> bool:
    return True

  def __str__(self, ) -> str:
    infoSpec = """[%d, %d]"""
    info = infoSpec % (self.row, self.col,)
    return textFmt(info)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d, %d)"""
    info = infoSpec % (type(self).__name__, self.row, self.col,)
    return textFmt(info)

  def __iter__(self, ) -> Iterator[int]:
    yield self.row
    yield self.col

  def _rollIndex(self, index: int) -> int:
    """Rolls integer index. """
    if index < 0:
      return self._rollIndex(index + len(self))
    if index < len(self):
      return index
    raise IndexError(index)

  def _resolveIndex(self, index: int) -> int:
    """Resolves integer index. """
    return self.col if self._rollIndex(index) % 2 else self.row

  def _resolveKey(self, key: str) -> int:
    """Resolves string key. """
    key = key.lower()
    if key in self.__row_keys__:
      return self.row
    if key in self.__col_keys__:
      return self.col
    raise KeyError(key)

  def __getitem__(self, identifier: Any) -> int:
    if isinstance(identifier, int):
      return self._resolveIndex(identifier)
    if isinstance(identifier, str):
      return self._resolveKey(identifier)
    raise TypeException('identifier', identifier, int, str, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, row: int, col: int, **kwargs) -> None:
    self.__row_id__ = row
    self.__col_id__ = col
    if kwargs:
      self.__init__(**kwargs)

  @overload(THIS)
  def __init__(self, other: Self, **kwargs) -> None:
    self.__init__(*other, **kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    for key in self.__row_keys__:
      if key in kwargs:
        value = kwargs[key]
        if isinstance(value, int):
          self.__row_id__ = value
          break
        raise TypeException(key, value, int, )
    for key in self.__col_keys__:
      if key in kwargs:
        value = kwargs[key]
        if isinstance(value, int):
          self.__col_id__ = value
          break
        raise TypeException(key, value, int, )
