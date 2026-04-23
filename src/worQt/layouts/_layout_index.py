"""
LayoutIndex provides a dataclass for indexing positions in a layout
manager. It has attributes 'row' and 'column' specifying the position of
the top-left corner and 'rowSpan' and 'colSpan' specifying the span of the
cell block.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.desc import WriteOnceError

from . import LayoutCell

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Union, Optional, TypeAlias, Self, Type

  Spans: TypeAlias = tuple[int, int]
  SpansField: TypeAlias = Union[Field, Spans]
  CellIter: TypeAlias = Iterator[LayoutCell]
  CellIterField: TypeAlias = Union[Field, Iterator[LayoutCell]]
  MaybeInt: TypeAlias = Optional[int]
  IntField: TypeAlias = Union[Field, int]
  CellField: TypeAlias = Union[Field, LayoutCell]
  NotImplementedType: TypeAlias = Type[NotImplemented]
  MaybeSelf: TypeAlias = Union[Self, NotImplementedType]
  IntIter: TypeAlias = Iterator[int]


class LayoutIndex(BaseObject, ):
  """
  LayoutIndex provides a dataclass for indexing positions in a layout
  manager. It has attributes 'row' and 'column' specifying the position of
  the top-left corner and 'rowSpan' and 'colSpan' specifying the span of the
  cell block.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_row__: int = 0
  __fallback_col__: int = 0
  __fallback_rowSpan__: int = 1
  __fallback_colSpan__: int = 1

  #  Private Variables
  __row_value__: MaybeInt = None
  __col_value__: MaybeInt = None
  __rowSpan_value__: MaybeInt = None
  __colSpan_value__: MaybeInt = None

  #  Public Variables
  row: IntField = Field()
  col: IntField = Field()
  rowSpan: IntField = Field()
  colSpan: IntField = Field()

  #  Virtual Variables
  cells: CellIterField = Field()
  top: IntField = Field()
  left: IntField = Field()
  bottom: IntField = Field()
  right: IntField = Field()
  spans: SpansField = Field()
  topLeft: CellField = Field()
  topRight: CellField = Field()
  bottomRight: CellField = Field()
  bottomLeft: CellField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @row.GET
  def _getRow(self, **kwargs) -> int:
    if self.__row_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.row = self.__fallback_row__
      return self._getRow(_recursion=True)
    if isinstance(self.__row_value__, int):
      return self.__row_value__
    raise TypeException('row', self.__row_value__, int)

  @col.GET
  def _getCol(self, **kwargs) -> int:
    if self.__col_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.col = self.__fallback_col__
      return self._getCol(_recursion=True)
    if isinstance(self.__col_value__, int):
      return self.__col_value__
    raise TypeException('col', self.__col_value__, int)

  @rowSpan.GET
  def _getRowSpan(self, **kwargs) -> int:
    if self.__rowSpan_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.rowSpan = self.__fallback_rowSpan__
      return self._getRowSpan(_recursion=True)
    if isinstance(self.__rowSpan_value__, int):
      return self.__rowSpan_value__
    raise TypeException('rowSpan', self.__rowSpan_value__, int)

  @colSpan.GET
  def _getColSpan(self, **kwargs) -> int:
    if self.__colSpan_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.colSpan = self.__fallback_colSpan__
      return self._getColSpan(_recursion=True)
    if isinstance(self.__colSpan_value__, int):
      return self.__colSpan_value__
    raise TypeException('colSpan', self.__colSpan_value__, int)

  @cells.GET
  def _getCells(self, ) -> CellIter:
    for r in range(self.rowSpan):
      for c in range(self.colSpan):
        yield LayoutCell(self.row + r, self.col + c, )

  @top.GET
  def _getTop(self, ) -> int:
    return self.row

  @left.GET
  def _getLeft(self, ) -> int:
    return self.col

  @bottom.GET
  def _getBottom(self, ) -> int:
    return self.row + self.rowSpan - 1

  @right.GET
  def _getRight(self, ) -> int:
    return self.col + self.colSpan - 1

  @spans.GET
  def _getSpans(self, ) -> tuple[int, int]:
    return self.rowSpan, self.colSpan

  @topLeft.GET
  def _getTopLeft(self, ) -> LayoutCell:
    return LayoutCell(self.row, self.col, )

  @topRight.GET
  def _getTopRight(self, ) -> LayoutCell:
    return LayoutCell(self.row, self.right, )

  @bottomRight.GET
  def _getBottomRight(self, ) -> LayoutCell:
    return LayoutCell(self.bottom, self.right, )

  @bottomLeft.GET
  def _getBottomLeft(self, ) -> LayoutCell:
    return LayoutCell(self.bottom, self.col, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @row.SET
  def _setRow(self, row: int) -> None:
    if self.__row_value__ is not None:
      raise WriteOnceError(self, self.__row_value__, row)
    if not isinstance(row, int):
      raise TypeException('row', row, int)
    self.__row_value__ = row

  @col.SET
  def _setCol(self, col: int) -> None:
    if self.__col_value__ is not None:
      raise WriteOnceError(self, self.__col_value__, col)
    if not isinstance(col, int):
      raise TypeException('col', col, int)
    self.__col_value__ = col

  @rowSpan.SET
  def _setRowSpan(self, rowSpan: int) -> None:
    if self.__rowSpan_value__ is not None:
      raise WriteOnceError(self, self.__rowSpan_value__, rowSpan)
    if not isinstance(rowSpan, int):
      raise TypeException('rowSpan', rowSpan, int)
    self.__rowSpan_value__ = rowSpan

  @colSpan.SET
  def _setColSpan(self, colSpan: int) -> None:
    if self.__colSpan_value__ is not None:
      raise WriteOnceError(self, self.__colSpan_value__, colSpan)
    if not isinstance(colSpan, int):
      raise TypeException('colSpan', colSpan, int)
    self.__colSpan_value__ = colSpan

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> IntIter:
    yield self.row
    yield self.col
    yield self.rowSpan
    yield self.colSpan

  @classmethod
  def _resolveOther(cls, other: Any) -> MaybeSelf:
    if isinstance(other, cls):
      return other
    try:
      resolved = cls(other)
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return resolved

  def __contains__(self, other: Any) -> bool:
    cls = type(self)
    if isinstance(other, cls):
      for cell in other.cells:
        if cell not in self:
          return False
      return True
    if isinstance(other, LayoutCell):
      for cell in self.cells:
        if cell == other:
          return True
    return False

  def __abs__(self, ) -> int:
    return self.rowSpan * self.colSpan

  def __bool__(self, ) -> bool:
    return True if abs(self) else False

  def __str__(self, ) -> str:
    if not self:
      return "<LayoutIndex: Empty>"
    clsName = type(self).__name__
    if abs(self) == 1:
      infoSpec = """<%s: (%d, %d)>"""
      info = infoSpec % (clsName, self.row, self.col)
      return textFmt(info)
    infoSpec = """<%s: rows: (%d, %d), columns: (%d, %d)>"""
    dims = self.top, self.bottom, self.left, self.right
    info = infoSpec % (clsName, *dims)
    return textFmt(info)

  def __repr__(self, ) -> str:
    if not self:
      infoSpec = """%s()"""
      clsName = type(self).__name__
      return infoSpec % (clsName,)
    if abs(self) == 1:
      infoSpec = """%s(%d, %d)"""
      clsName = type(self).__name__
      return infoSpec % (clsName, self.row, self.col)
    infoSpec = """%s(%d, %d, %d, %d)"""
    clsName = type(self).__name__
    dims = self.row, self.col, self.rowSpan, self.colSpan
    return infoSpec % (clsName, *dims)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int, )
  def __init__(self, row: int, col: int, rowSpan: int, colSpan: int) -> None:
    self.row = row
    self.col = col
    self.rowSpan = rowSpan
    self.colSpan = colSpan

  @overload(int, int, )
  def __init__(self, row: int, col: int) -> None:
    self.row = row
    self.col = col

  @overload()
  def __init__(self, ) -> None:
    pass

  @overload(LayoutCell)
  def __init__(self, cell: LayoutCell) -> None:
    self.row = cell.row
    self.col = cell.col

  @overload(LayoutCell, LayoutCell, )
  def __init__(self, topLeft: LayoutCell, bottomRight: LayoutCell) -> None:
    self.row = topLeft.row
    self.col = topLeft.col
    self.rowSpan = bottomRight.row - topLeft.row + 1
    self.colSpan = bottomRight.col - topLeft.col + 1
