"""
LayoutManager provides the central layout management class for managing
'worQt' widgets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout, QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject, BaseMeta
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import MissingVariable, TypeException

from worQt.layouts import LayoutIndex, LayoutCell, LayoutItem, LayoutEntry, \
  LayoutNULL

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Union, Optional, Iterator

  Entries: TypeAlias = tuple[LayoutEntry, ...]
  RowCol: TypeAlias = Union[tuple[int, int], list[int]]


class LayoutManager(metaclass=BaseMeta):
  """
  LayoutManager provides the central layout management class for managing
  'worQt' widgets.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __parent_instance__ = None
  __base_widget__ = None
  __layout_entries__ = None

  #  Public Variables
  parent = Field()
  base = Field()
  entries = Field()

  #  Virtual Variables
  Q = Field()
  width = Field()
  height = Field()
  nullCells = Field()
  boundaryCells = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @parent.GET
  def _getParent(self, ) -> QWidget:
    if self.__parent_instance__ is None:
      raise MissingVariable(self, '__parent_instance__', QWidget)
    if isinstance(self.__parent_instance__, QWidget):
      return self.__parent_instance__
    name, value = '__parent_instance__', self.__parent_instance__
    raise TypeException(name, value, QWidget)

  @base.GET
  def _getBase(self, **kwargs) -> QWidget:
    raise NotImplementedError

  @entries.GET
  def _getEntries(self, ) -> Entries:
    return maybe(self.__layout_entries__, ())

  @Q.GET
  def _getQGridLayout(self, ) -> QGridLayout:
    """
    Creates a QGridLayout instance with all the widgets added to this
    layout manager.
    """
    raise NotImplementedError

  @width.GET
  def _getWidth(self, ) -> int:
    out = 0
    for index, item in self.entries:
      out = max(out, index.right)
    return out + 1

  @height.GET
  def _getHeight(self, ) -> int:
    out = 0
    for index, item in self.entries:
      out = max(out, index.bottom)
    return out + 1

  @nullCells.GET
  def _getNullCells(self, ) -> Iterator[LayoutNULL]:
    for cell in self:
      if isinstance(cell, LayoutNULL):
        yield cell

  @boundaryCells.GET
  def _getBoundaryCells(self, ) -> Iterator[LayoutNULL]:
    for null in self.nullCells:
      yield null
    col0, row0 = self.width, self.height
    for row in range(self.height + 1):
      yield LayoutNULL(LayoutCell(row, col0))
    for col in range(self.width + 1):
      yield LayoutNULL(LayoutCell(row0, col))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __getitem__(self, identifier: Any) -> LayoutItem:
    if isinstance(identifier, LayoutIndex):
      return self._resolveIndex(identifier)
    if isinstance(identifier, LayoutCell):
      return self._resolveCell(identifier)
    if isinstance(identifier, (tuple, list)):
      return self._resolveTuple(identifier)
    types = LayoutIndex, LayoutCell, tuple, list
    raise TypeException('identifier', identifier, *types)

  def __setitem__(self, index: LayoutIndex, item: LayoutItem, ) -> None:
    if not isinstance(index, LayoutIndex):
      raise TypeException('index', index, LayoutIndex)
    if not isinstance(item, LayoutItem):
      raise TypeException('item', item, LayoutItem)
    self.__layout_entries__ = (*self.entries, LayoutEntry(index, item),)

  def __iter__(self, ) -> Iterator[LayoutCell]:
    for row in range(self.height):
      for col in range(self.width):
        cell = LayoutCell(row, col)
        for index, item in self.entries:
          if cell in index:
            yield cell
            break
        else:
          yield LayoutNULL(cell)

  def __contains__(self, other: Any) -> bool:
    if isinstance(other, LayoutEntry):
      return other.index in self
    if isinstance(other, LayoutIndex):
      for cell in other:
        if cell in self:
          continue
        return False
      return True
    if isinstance(other, LayoutCell):
      return True if other in self.nullCells else False
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, parent: QWidget, *args, **kwargs) -> None:
    if not isinstance(parent, QWidget):
      raise TypeException('parent', parent, QWidget)
    self.__parent_instance__ = parent

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _validateIndex(self, index: LayoutIndex) -> None:
    raise NotImplementedError

  def _resolveIndex(self, index: LayoutIndex) -> LayoutItem:
    for entry in self.entries:
      if entry.index == index:
        return entry.item
    raise IndexError(index)

  def _resolveCell(self, cell: LayoutCell) -> LayoutItem:
    for entry in self.entries:
      if cell in entry.index:
        return entry.item
    raise IndexError(cell)

  def _resolveTuple(self, rowCol: RowCol) -> LayoutItem:
    if len(rowCol) != 2:
      infoSpec = """Expected tuple of length 2, got length %d!"""
      info = infoSpec % len(rowCol)
      raise ValueError(textFmt(info))
    row, col = rowCol
    cell = LayoutCell(row, col)
    return self._resolveCell(cell)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  NOTE
  #  If the general widget entry class can be defined without reference to
  #  the layout package, then 'QWidget' in the below overloads should be
  #  replaced. In either case, the 'overload' system provided by 'worktoy'
  #  is sufficiently robust to match against subclasses, albeit slightly
  #  slower. This speed concern is negligible as it occurs only during
  #  setup. To achieve best performance, the overload system needs the
  #  signature class to be identical to the argument class, allowing for
  #  hash-based dispatch.

  @overload(QWidget)
  def addWidget(self, widget: QWidget) -> None:
    """
    This overload places the widget in the next available cell assigning
    to it a span of (1, 1).
    """
    raise NotImplementedError

  @overload(QWidget, LayoutCell)
  def addWidget(self, widget: QWidget, cell: LayoutCell) -> None:
    """
    This overload places the widget in the specified cell assigning to it
    a span of (1, 1).
    """
    raise NotImplementedError

  @overload(QWidget, LayoutSpan)
  def addWidget(self, widget: QWidget, span: LayoutSpan) -> None:
    """
    This overload adds the widget with the specified span in the next
    available span of cells.
    """
    raise NotImplementedError

  @overload(QWidget, int, int)
  def addWidget(self, widget: QWidget, row: int, col: int) -> None:
    raise NotImplementedError

  @overload(QWidget, LayoutIndex)
  def addWidget(self, widget: QWidget, index: LayoutIndex) -> None:
    """
    This overload adds the widget as specified by the given index.
    """
    raise NotImplementedError

  @overload(QWidget, int, int, int, int)
  def addWidget(self, widget: QWidget, *args: int) -> None:
    raise NotImplementedError

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
