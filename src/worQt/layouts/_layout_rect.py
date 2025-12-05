"""
LayoutRect encapsulates a rectangular region within a layout. It combines
the 'LayoutIndex' and 'LayoutSpan' classes and represents the indices
spanning from a 'LayoutIndex' object over a 'LayoutSpan' object.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import textFmt

from moreworktoy.mcls import BaseObject

from . import LayoutIndex, LayoutSpan
from ..waitaminute import EmptyLayoutException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, TypeAlias, Iterator

  Index: TypeAlias = LayoutIndex
  Span: TypeAlias = LayoutSpan


class LayoutRect(BaseObject):
  """
  LayoutRect encapsulates a rectangular region within a layout. It combines
  the 'LayoutIndex' and 'LayoutSpan' classes and represents the indices
  spanning from a 'LayoutIndex' object over a 'LayoutSpan' object.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __index_keys__ = ('index', 'idx', 'i',)
  __span_keys__ = ('span', 'spn', 's',)

  #  Fallback Variables

  #  Private Variables
  __layout_index__ = None
  __layout_span__ = None

  #  Public Variables
  index = Field()
  span = Field()

  #  Virtual Variables
  last = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @index.GET
  def _getIndex(self, **kwargs) -> Index:
    if self:
      if self.__layout_index__ is None:
        if kwargs.get('_recursion', False):
          raise RecursionError
        self.__layout_index__ = LayoutIndex()
        return self._getIndex(_recursion=True)
      return self.__layout_index__
    raise EmptyLayoutException

  @span.GET
  def _getSpan(self, **kwargs) -> Span:
    if self.__layout_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__layout_span__ = LayoutSpan()
      return self._getSpan(_recursion=True)
    return self.__layout_span__

  @last.GET
  def _getLast(self, **kwargs) -> Index:
    if self:
      row = self.index.row + self.span.rows - 1
      col = self.index.col + self.span.cols - 1
      return LayoutIndex(row, col)
    raise EmptyLayoutException

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _containsIndex(self, index: Index) -> bool:
    if not self:
      return False
    if index.row < self.index.row or index.row > self.last.row:
      return False
    if index.col < self.index.col or index.col > self.last.col:
      return False
    return True

  def _containsOther(self, other: Self) -> bool:
    if not self:
      return False
    return True if other.index in self and other.last in self else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Index]:
    if self:
      r0, c0 = self.index
      for r in range(self.span.rows):
        for c in range(self.span.cols):
          yield LayoutIndex(r0 + r, c0 + c)

  def __abs__(self, ) -> int:
    return abs(self.span)

  def __len__(self, ) -> int:
    return abs(self)

  def __eq__(self, other: Any) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self.index != other.index:
      return False
    if self.span != other.span:
      return False
    return True

  def __hash__(self, ) -> int:
    return hash((hash(self.index), hash(self.span),))

  def __contains__(self, other: Any) -> bool:
    if isinstance(other, LayoutIndex):
      return self._containsIndex(other)
    cls = type(self)
    if isinstance(other, cls):
      return self._containsOther(other)
    return False

  def __str__(self, ) -> str:
    if not self:
      infoSpec = """%s object representing an empty layout rectangle."""
      info = infoSpec % (type(self).__name__,)
      return textFmt(info)
    if len(self) == 1:
      infoSpec = """%s object at row %d and column %d."""
      info = infoSpec % (
          type(self).__name__,
          self.index.row,
          self.index.col,
      )
      return textFmt(info)
    infoSpec = """
      %s object spanning rows %d to %d inclusive and columns 
      %d to %d inclusive.
    """
    clsName = type(self).__name__
    r0, r1 = self.index.row, self.last.row
    c0, c1 = self.index.col, self.last.col
    info = infoSpec % (clsName, r0, r1, c0, c1,)
    return textFmt(info)

  def __repr__(self, ) -> str:
    infoSpec = """%s(%s, %s)"""
    clsName = type(self).__name__
    indexRepr = repr(self.index)
    spanRepr = repr(self.span)
    info = infoSpec % (clsName, indexRepr, spanRepr,)
    return textFmt(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload()
  def __init__(self, **kwargs) -> None:
    for key, value in kwargs.items():
      if key.lower() in self.__index_keys__:
        self.__layout_index__ = value
      elif key.lower() in self.__span_keys__:
        self.__layout_span__ = value

  @overload(int, int)  # Assumes row and column
  def __init__(self, row: int, col: int, **kwargs) -> None:
    self.__layout_index__ = LayoutIndex(row, col)
    if kwargs:
      self.__init__(**kwargs)

  @overload(LayoutIndex)
  def __init__(self, index: Index, **kwargs) -> None:
    self.__layout_index__ = index
    if kwargs:
      self.__init__(**kwargs)

  @overload(LayoutSpan)
  def __init__(self, span: Span, **kwargs) -> None:
    self.__layout_span__ = span
    if kwargs:
      self.__init__(**kwargs)

  @overload(LayoutIndex, LayoutSpan)
  def __init__(self, index: Index, span: Span, **kwargs) -> None:
    self.__layout_index__ = index
    self.__layout_span__ = span
    if kwargs:
      self.__init__(**kwargs)

  @overload(LayoutSpan, LayoutIndex)
  def __init__(self, span: Span, index: Index, **kwargs) -> None:
    self.__init__(index, span, **kwargs)

  @overload(int, int, int, int)
  def __init__(self, *args, **kwargs) -> None:
    row, col, rowSpan, colSpan = args
    self.__layout_index__ = LayoutIndex(row, col)
    self.__layout_span__ = LayoutSpan(rowSpan, colSpan)
    if kwargs:
      self.__init__(**kwargs)

  @overload(int, int, LayoutSpan)
  def __init__(self, row: int, col: int, span: Span, **kwargs) -> None:
    self.__layout_index__ = LayoutIndex(row, col)
    self.__layout_span__ = span
    if kwargs:
      self.__init__(**kwargs)

  @overload(LayoutIndex, int, int)
  def __init__(self, index: Index, *args, **kwargs) -> None:
    rowSpan, colSpan = args
    self.__layout_index__ = index
    self.__layout_span__ = LayoutSpan(rowSpan, colSpan)
    if kwargs:
      self.__init__(**kwargs)

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
