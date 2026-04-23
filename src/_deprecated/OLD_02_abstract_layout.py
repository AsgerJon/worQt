"""
AbstractLayout provides the central layout management class for managing
'worQt' widgets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout, QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import TypeException

from worQt.layouts import LayoutCell, LayoutIndex, LayoutMixin

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Self


class AbstractLayout(QGridLayout, LayoutMixin):
  """
  AbstractLayout provides the central layout management class for managing
  'worQt' widgets.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __registered_widgets__ = None

  #  Public Variables

  #  Virtual Variables
  top = Field()
  left = Field()
  bottom = Field()
  right = Field()
  rowSpacing = Field()
  colSpacing = Field()
  cells = Field()
  asIndex = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRegisteredWidgets(self, ) -> dict[LayoutIndex, QWidget]:
    return maybe(self.__registered_widgets__, dict(), )

  @top.GET
  def _getTop(self, ) -> int:
    if not self:
      return 0
    out = None
    for index in self:
      for cell in index.cells:
        if out is None:
          out = cell.row
          continue
        out = min(out, cell.row)
    return maybe(out, 0)

  @left.GET
  def _getLeft(self, ) -> int:
    if not self:
      return 0
    out = None
    for index in self:
      for cell in index.cells:
        if out is None:
          out = cell.col
          continue
        out = min(out, cell.col)
    return maybe(out, 0)

  @bottom.GET
  def _getBottom(self, ) -> int:
    if not self:
      return 0
    out = None
    for index in self:
      for cell in index.cells:
        if out is None:
          out = cell.row
          continue
        out = max(out, cell.row)
    return maybe(out, 0)

  @right.GET
  def _getRight(self, ) -> int:
    if not self:
      return 0
    out = None
    for index in self:
      for cell in index.cells:
        if out is None:
          out = cell.col
          continue
        out = max(out, cell.col)
    return maybe(out, 0)

  @rowSpacing.GET
  def _getRowSpacing(self, ) -> int:
    if not self:
      return 0
    return self.bottom - self.top + 1

  @colSpacing.GET
  def _getColSpacing(self, ) -> int:
    if not self:
      return 0
    return self.right - self.left + 1

  @cells.GET
  def _getCells(self, ) -> Iterator[LayoutCell]:
    for r in range(self.rowSpacing):
      for c in range(self.colSpacing):
        yield LayoutCell(self.top + r, self.left + c, )

  @asIndex.GET
  def _getAsIndex(self, ) -> LayoutIndex:
    return LayoutIndex(self.top, self.left, self.rowSpacing,
                       self.colSpacing, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[LayoutIndex]:
    registered = self._getRegisteredWidgets()
    for index in registered.keys():
      yield index

  def _resolveIndex(self, index: LayoutIndex) -> QWidget:
    registered = self._getRegisteredWidgets()
    if index in registered:
      return registered[index]
    raise NotImplementedError

  def _resolveCell(self, cell: LayoutCell) -> QWidget:
    registered = self._getRegisteredWidgets()
    for index, widget in registered.items():
      if cell in index:
        return widget
    raise NotImplementedError

  def __contains__(self, index: LayoutIndex) -> bool:
    """
    This method checks if the provided index is present in the widget
    registry of this layout.
    """
    return True if index in self._getRegisteredWidgets() else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, ) -> None:
    parent = self._resolveParent(*args, )
    if parent is None:
      QGridLayout.__init__(self, )
    elif isinstance(parent, QWidget):
      QGridLayout.__init__(self, parent, )
    else:
      raise TypeException('parent', parent, QWidget, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _registerWidget(self, widget: QWidget, *args) -> LayoutIndex:
    row, col, rows, cols = None, None, None, None
    for arg in args:
      if isinstance(arg, int):
        if row is None:
          row = arg
        elif col is None:
          col = arg
        elif rows is None:
          rows = arg
        elif cols is None:
          cols = arg
    if (row is None) ^ (col is None):
      infoSpec = """%s._registerWidget() missing 1 required positional 
      argument: 'col' when 'row' is provided (received: '%d')!"""
      clsName = type(self).__name__
      info = textFmt(infoSpec % (clsName, row))
      raise TypeError(info)
    if row is None:
      cell = self._autoPlaceWidget(widget)
      row, col = cell.row, cell.col
    rows, cols = maybe(rows, 1), maybe(cols, 1)
    index = LayoutIndex(row, col, rows, cols, )
    existing = self._getRegisteredWidgets()
    existing[index] = widget
    self.__registered_widgets__ = existing
    return index

  @overload(int, int)
  def _expandedCells(self, rows: int, cols: int) -> Iterator[LayoutCell]:
    """
    This method iterates over cells in self, but expanded to include the
    rows and columns specified.
    """
    diagonals = max(self.rowSpan + rows, self.colSpan + cols)
    for d in range(diagonals):
      r = d
      for c in range(d):
        if r < self.rowSpan + rows and c < self.colSpan + cols:
          yield LayoutCell(self.top + r, self.left + c, )
      c = d
      for r in range(d):
        if r < self.rowSpan + rows and c < self.colSpan + cols:
          yield LayoutCell(self.top + r, self.left + c, )

  @overload(LayoutIndex)
  def _expandedCells(self, index: LayoutIndex) -> Iterator[LayoutCell]:
    return self._expandedCells(index.rowSpan, index.colSpan, )

  @overload(THIS)
  def _expandedCells(self, other: Self) -> Iterator[LayoutCell]:
    if isinstance(other.asIndex, LayoutIndex):
      return self._expandedCells(other.asIndex, )
    name, value = 'other.asIndex', other.asIndex
    raise TypeException(name, value, LayoutIndex, )

  def _boundsCheck(self, other: Any) -> bool:
    """
    This method checks if the provided cell or index is within the current
    bounds of this layout. It does not check for availability.
    """
    cls = type(self)
    if isinstance(other, cls):
      for index in other:
        if not self._boundsCheck(index):
          return False
      return True
    if isinstance(other, LayoutIndex):
      for cell in other.cells:
        if not self._boundsCheck(cell):
          return False
      return True
    if isinstance(other, LayoutCell):
      if not (self.top <= other.row <= self.bottom):
        return False
      if not (self.left <= other.col <= self.right):
        return False
      return True
    raise TypeException('other', other, LayoutCell, LayoutIndex, cls, )

  def _availabilityCheck(self, other: Any) -> bool:
    """
    This method checks if the provided index or cell is already occupied
    in this layout.
    """
    if not self._boundsCheck(other):
      return False
    if isinstance(other, LayoutIndex):
      if other in self:
        return False
      for cell in other.cells:
        if not self._availabilityCheck(cell):
          return False
      return True
    if isinstance(other, LayoutCell):
      for index in self:
        if other in index:
          return False
      return True
    raise TypeException('other', other, LayoutCell, LayoutIndex, )

  def _fitItem(self, other: Any) -> LayoutIndex:
    """
    This method fits 'other' in available cells in layout, possibly by
    expanding it and returns the fitted index. It supports the following
    argument signatures:
    - _Cell:  Is treated like a single-cell _Index object.
    - _Index: Is expanded to fit available space in layout.
    - Self: Fits the 'other.asIndex' _Index object.
    Return:
    - _Index: The fitted index.
    """
    cls = type(self)
    if isinstance(other, cls):
      return self._fitItem(other.asIndex)
    if isinstance(other, LayoutIndex):
      spans = other.rowSpan, other.colSpan
      expanded = self._expandedCells(other)
      for cell in expanded:
        testIndex = LayoutIndex(cell.row, cell.col, *spans, )
        if self._availabilityCheck(testIndex):
          return testIndex
      infoSpec = """Could not fit %s in %s!"""
      info = textFmt(infoSpec % (other, type(self).__name__,))
      raise ValueError(info)
    if isinstance(other, LayoutCell):
      return self._fitItem(LayoutIndex(other.row, other.col, 1, 1, ))
    raise TypeException('other', other, LayoutCell, LayoutIndex, cls, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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

  def addWidget(self, widget: QWidget, *args, ) -> None:
    intArgs = [arg for arg in args if isinstance(arg, int)]
    noneArgs = [None for _ in range(4)]
    row, col, rowSpan, colSpan = [*intArgs, *noneArgs, ][:4]
    rowSpan, colSpan = maybe(rowSpan, 1), maybe(colSpan, 1)
    if (row is None) ^ (col is None):
      infoSpec = """%s.addWidget() missing 1 required positional argument: 
      'col' when 'row' is provided (received: '%d')!"""
      clsName = type(self).__name__
      info = textFmt(infoSpec % (clsName, row))
      raise TypeError(info)
    if row is None:  # Implement auto placement
      index = self._fitItem(LayoutIndex(0, 0, rowSpan, colSpan, ))
      row, col = index.row, index.col
    self._registerWidget(widget, row, col, rowSpan, colSpan, )
    QGridLayout.addWidget(self, widget, row, col, rowSpan, colSpan, )
