"""
LayoutIndex provides an index for entries in a layout grid.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

import sys

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt, typeCast
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.dispatch import TypeCastException

from moreworktoy.utilities import validateIterable
from worQt.layouts import LayoutCell

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Iterator, Type

eps: float = sys.float_info.epsilon


class LayoutIndex(BaseObject):
  """
  LayoutIndex provides an index for entries in a layout grid.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __top_fallback__ = 0
  __left_fallback__ = 0
  __fallback_row_span__ = 1
  __fallback_col_span__ = 1

  #  Private Variables
  __top_row__ = None
  __left_col__ = None
  __row_span__ = None
  __col_span__ = None

  #  Public Variables
  top = Field()
  left = Field()
  rowSpan = Field()
  colSpan = Field()

  #  Virtual Variables
  bottom = Field()
  right = Field()
  height = Field()
  width = Field()
  cellCount = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @left.GET
  def _getLeft(self, **kwargs) -> int:
    if self.__left_col__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__left_col__ = self.__left_fallback__
      return self._getLeft(_recursion=True)
    return self.__left_col__

  @right.GET
  def _getRight(self, **kwargs) -> int:
    if self.__right_col__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__right_col__ = self.__right_fallback__
      return self._getRight(_recursion=True)
    return self.__right_col__

  @rowSpan.GET
  def _getRowSpan(self, **kwargs) -> int:
    if self.__row_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__row_span__ = self.__fallback_row_span__
      return self._getRowSpan(_recursion=True)
    if isinstance(self.__row_span__, int):
      if self.__row_span__ < 0:
        infoSpec = """Row span cannot be negative, but received '%d'!"""
        info = textFmt(infoSpec % self.__row_span__)
        raise ValueError(info)
      return self.__row_span__
    raise TypeException('__row_span__', self.__row_span__, int, )

  @colSpan.GET
  def _getColSpan(self, **kwargs) -> int:
    if self.__col_span__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__col_span__ = self.__fallback_col_span__
      return self._getColSpan(_recursion=True)
    if isinstance(self.__col_span__, int):
      if self.__col_span__ < 0:
        infoSpec = """Column span cannot be negative, but received '%d'!"""
        info = textFmt(infoSpec % self.__col_span__)
        raise ValueError(info)
      return self.__col_span__
    raise TypeException('__col_span__', self.__col_span__, int, )

  @bottom.GET
  def _getBottom(self, **kwargs) -> int:
    return self.top + self.rowSpan - 1

  @right.GET
  def _getRight(self, **kwargs) -> int:
    return self.left + self.colSpan - 1

  @height.GET
  def _getHeight(self, **kwargs) -> int:
    return self.rowSpan

  @width.GET
  def _getWidth(self, **kwargs) -> int:
    return self.colSpan

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __abs__(self, ) -> int:
    """
    The absolute value of a LayoutIndex is the number of cells it spans.
    """
    return self.nRows * self.nCols

  def __iter__(self, ) -> Iterator[Self]:
    """
    Iterating over a LayoutIndex yields the individual cell indices it spans.
    """
    rows = (*range(self.top, self.bottom + 1),)
    cols = (*range(self.left, self.right + 1),)
    for row in rows:
      for col in cols:
        yield LayoutCell(col, row)

  def __bool__(self, ) -> bool:
    """
    A LayoutIndex is considered True if it spans at least one cell.
    """
    return True if self.nRows and self.nCols else False

  def __len__(self, ) -> int:
    """
    The length is 2, the number of dimensions.
    """
    return 2

  #  Binary operations
  def _resolveOther(self, other: Any) -> Self:
    cls = type(self)
    if isinstance(other, cls):
      return other
    try:
      other = cls(other)
    except (ValueError, TypeError) as exception:
      # Either is assumed to mean failure to instantiate
      return NotImplemented
    else:
      if isinstance(other, cls):
        return other
      raise TypeException('other', other, cls)
    finally:
      pass

  def __eq__(self, other: Any) -> bool:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self and other:
      if self.left - other.left:
        return False
      if self.right - other.right:
        return False
      if self.top - other.top:
        return False
      if self.bottom - other.bottom:
        return False
      return True
    return False

  def __ne__(self, other: Any) -> bool:
    if self.__eq__(other) is NotImplemented:
      return NotImplemented
    return False if self == other else True

  #  ________________________________________________________________________
  #  ADDITION

  def __add__(self, other: Any) -> Self:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    left = min(self.left, other.left)
    right = max(self.right, other.right)
    top = min(self.top, other.top)
    bottom = max(self.bottom, other.bottom)
    cls = type(self)
    return cls(left, top, right, bottom)

  def __radd__(self, other: Any) -> Self:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self + other

  def __iadd__(self, other: Any) -> Self:
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    combined = self + other
    self.__left_col__ = combined.left
    self.__right_col__ = combined.right
    self.__top_row__ = combined.top
    self.__bottom_row__ = combined.bottom
    return self

  #
  #  ¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨
  #
  #  ________________________________________________________________________
  #  SUBTRACTION
  #  Subtraction is understood to meant the region of cells in self,
  #  but not in other. If every cell in self is also in other, an empty
  #  instance is returned. Negative indices are undefined. Otherwise,
  #  the return value depends on the cells in self not in other. If these
  #  fit exactly into one rectangular region, that is returned. Otherwise,
  #  the most top-left cell is chosen with row priority (the top cell of
  #  the cells in the left-most column). The largest rectangular region
  #  starting from that cell and fitting within the remaining cells is
  #  returned.

  def __sub__(self, other: Any) -> Self:
    raise NotImplementedError

  #
  #  ¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨
  #
  #  ________________________________________________________________________
  #  MULTIPLICATION
  #  Multiplication is understood to mean the intersection between 'self'
  #  and 'other'. If there is no intersection, an empty instance is returned.
  #
  #  If 'other' is not a LayoutIndex, but is an integer or a pair of
  #  integers, then multiplication is taken to mean scaling both dimensions
  #  by that factor or those factors respectively.

  def _interSection(self, other: Self) -> Self:
    """
    This private method actually implements the intersection between 'self'
    and 'other'.
    """
    cls = type(self)
    left = max(self.left, other.left)
    right = min(self.right, other.right)
    top = max(self.top, other.top)
    bottom = min(self.bottom, other.bottom)
    if left < right and top < bottom:
      return cls(left, top, right, bottom)
    return cls()

  def _scaled(self, *args, ) -> Self:
    """
    This private method actually implements the scaling of 'self' by
    integer factors.
    """
    rowScale, colScale, *_ = [*args, None, None]
    if rowScale is None:  # Received no scaling factors
      infoSpec = """'%s._scaled' require at least one scaling factor!"""
      info = textFmt(infoSpec % type(self).__name__)
      raise ValueError(info)
    if colScale is None:  # Received one scaling factor
      colScale = rowScale
    cls = type(self)
    if not rowScale * colScale:
      return cls()
    if min([rowScale, colScale, 0]):
      infoSpec = """Scaling factors must be non-negative integers, 
      but received '%d' and '%d'!"""
      info = textFmt(infoSpec % (colScale, rowScale))
      raise ValueError(info)
    right = self.left + (self.nCols * colScale) - 1
    bottom = self.top + (self.nRows * rowScale) - 1
    return cls(self.left, self.top, right, bottom)

  def __mul__(self, other: Any) -> Self:
    other_ = self._resolveOther(other)
    if other_ is NotImplemented:
      if validateIterable(other):
        try:
          out = self._scaled(*other)
        except ValueError:
          return NotImplemented
        else:
          return out
      try:
        other_ = typeCast(int, other)
      except TypeCastException:
        return NotImplemented
      else:
        return self._scaled(other_)
    return self._interSection(other_)

  def __rmul__(self, other: Any) -> Self:
    """Because of commutativity, simply fall back to __mul__."""
    return self * other

  def __imul__(self, other: Any) -> Self:
    tmp = self * other
    if tmp is NotImplemented:
      return NotImplemented
    self.__left_col__ = tmp.left
    self.__right_col__ = tmp.right
    self.__top_row__ = tmp.top
    self.__bottom_row__ = tmp.bottom
    return self

  #
  #  ¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨¨
  #
  #  ________________________________________________________________________
  #  MATRIX MULTIPLICATION
  #  The '@' operator scales 'self' by the dimensions of 'other'. For
  #  example:
  #  self = LayoutIndex(1, 1, 2, 3)  # 2 rows, 3 columns
  #  other = LayoutIndex(0, 0, 1, 2)  # 1 row, 2 columns
  #  result = self @ other  # LayoutIndex(1, 1, 2, 6)  # 2 rows, 6 columns
  #
  #  The result will be placed on the same top-left cell as 'self'.
  #
  #  If 'other' is not a LayoutIndex, '@' falls back to normal
  #  multiplication.
  #

  def __matmul__(self, other: Any) -> Self:
    other_ = self._resolveOther(other)
    if other_ is NotImplemented:
      return self * other
    cls = type(self)
    nRows = self.nRows * other_.nRows
    nCols = self.nCols * other_.nCols
    right = self.left + nCols - 1
    bottom = self.top + nRows - 1
    return cls(self.left, self.top, right, bottom)

  def __imatmul__(self, other: Any) -> Self:
    tmp = self @ other
    if tmp is NotImplemented:
      return NotImplemented
    self.__left_col__ = tmp.left
    self.__right_col__ = tmp.right
    self.__top_row__ = tmp.top
    self.__bottom_row__ = tmp.bottom
    return self

  def __rmatmul__(self, other: Any) -> Self:
    other_ = self._resolveOther(other)
    if other_ is NotImplemented:
      return self * other
    return other_ @ self

  def __contains__(self, other: Self) -> bool:
    """
    A LayoutIndex contains another LayoutIndex if all cells in the other
    are also in self.
    """
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not other:
      return False
    if abs(other) != 1:
      for cell in other:
        if cell not in self:
          return False
      return True
    #  Only single cell indices remain to be checked
    x, y = other.left, other.top
    if self.left <= x <= self.right:
      if self.top <= y <= self.bottom:
        return True
    return False

  def __hash__(self, ) -> int:
    return hash((self.top, self.left, self.rowSpan, self.colSpan,))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)  # row, col, rowSpan, colSpan
  def __init__(self, *args) -> None:
    row, col, rowSpan, colSpan = args
    self.__top_row__ = row
    self.__left_col__ = col
    self.__row_span__ = rowSpan
    self.__col_span__ = colSpan

  @overload(int, int)  # Defaults to rowSpan=1, colSpan=1
  def __init__(self, row: int, col: int) -> None:
    self.__init__(col, row, 1, 1, )

  @overload()  # Defaults to 0, 0, 0, 0, an empty LayoutIndex
  def __init__(self, ) -> None:
    pass

  @overload(THIS)  # Copies other
  def __init__(self, other: Self) -> None:
    self.__init__(other.left, other.top, other.width, other.height, )

  @overload(LayoutCell)
  def __init__(self, cell: LayoutCell) -> None:
    self.__init__(cell.row, cell.col, 1, 1, )

  @classmethod
  def fromCells(cls: Type[Self], *cells: Self) -> Self:
    """
    Construct a LayoutIndex from a list of cell coordinates.
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
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
