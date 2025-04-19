"""LayoutRect represents a rectangle in a layout."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field
from worktoy.mcls import BaseObject
from worktoy.static import overload, THIS
from worktoy.text import typeMsg
from worktoy.waitaminute import MissingVariable, ReadOnlyError

from moreworktoy.waitaminute import WriteOnceError
from . import LayoutIndex, LayoutSpan

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Self


class LayoutRect(BaseObject):
  """LayoutRect represents a rectangle in a layout."""

  __iter_contents__ = None
  __set_key__ = None

  #  private variables
  __left_col__ = None
  __top_row__ = None
  __right_col__ = None
  __bottom_row__ = None

  #  public fields
  left = Field()
  top = Field()
  right = Field()
  bottom = Field()

  #  virtual fields
  colSpan = Field()
  rowSpan = Field()
  topLeft = Field()
  topRight = Field()
  bottomRight = Field()
  bottomLeft = Field()
  width = Field()
  height = Field()
  span = Field()

  @left.GET
  def _getLeft(self) -> int:
    """Get the left column index."""
    if self.__left_col__ is None:
      raise MissingVariable('__left_col__', int)
    if isinstance(self.__left_col__, int):
      return self.__left_col__
    raise TypeError(typeMsg('__left_col__', self.__left_col__, int))

  @left.SET
  def _setLeft(self, value: int) -> None:
    """Set the left column index."""
    if self.__left_col__ is not None:
      raise WriteOnceError('__left_col__', self.__left_col__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__left_col__', value, int))
    self.__left_col__ = value

  @top.GET
  def _getTop(self) -> int:
    """Get the top row index."""
    if self.__top_row__ is None:
      raise MissingVariable('__top_row__', int)
    if isinstance(self.__top_row__, int):
      return self.__top_row__
    raise TypeError(typeMsg('__top_row__', self.__top_row__, int))

  @top.SET
  def _setTop(self, value: int) -> None:
    """Set the top row index."""
    if self.__top_row__ is not None:
      raise WriteOnceError('__top_row__', self.__top_row__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__top_row__', value, int))
    self.__top_row__ = value

  @right.GET
  def _getRight(self) -> int:
    """Get the right column index."""
    if self.__right_col__ is None:
      raise MissingVariable('__right_col__', int)
    if isinstance(self.__right_col__, int):
      return self.__right_col__
    raise TypeError(typeMsg('__right_col__', self.__right_col__, int))

  @right.SET
  def _setRight(self, value: int) -> None:
    """Set the right column index."""
    if self.__right_col__ is not None:
      raise WriteOnceError('__right_col__', self.__right_col__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__right_col__', value, int))
    self.__right_col__ = value

  @bottom.GET
  def _getBottom(self) -> int:
    """Get the bottom row index."""
    if self.__bottom_row__ is None:
      raise MissingVariable('__bottom_row__', int)
    if isinstance(self.__bottom_row__, int):
      return self.__bottom_row__
    raise TypeError(typeMsg('__bottom_row__', self.__bottom_row__, int))

  @bottom.SET
  def _setBottom(self, value: int) -> None:
    """Set the bottom row index."""
    if self.__bottom_row__ is not None:
      raise WriteOnceError('__bottom_row__', self.__bottom_row__, value)
    if not isinstance(value, int):
      raise TypeError(typeMsg('__bottom_row__', value, int))
    self.__bottom_row__ = value

  @width.GET
  @colSpan.GET
  def _getColSpan(self) -> int:
    """Get the column span."""
    return self.right - self.left + 1

  @height.GET
  @rowSpan.GET
  def _getRowSpan(self) -> int:
    """Get the row span."""
    return self.bottom - self.top + 1

  @topLeft.GET
  def _getTopLeft(self) -> LayoutIndex:
    """Get the top left corner of the rectangle."""
    return LayoutIndex(self.left, self.top)

  @topRight.GET
  def _getTopRight(self) -> LayoutIndex:
    """Get the top right corner of the rectangle."""
    return LayoutIndex(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self) -> LayoutIndex:
    """Get the bottom right corner of the rectangle."""
    return LayoutIndex(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self) -> LayoutIndex:
    """Get the bottom left corner of the rectangle."""
    return LayoutIndex(self.left, self.bottom)

  @span.GET
  def _getSpan(self) -> LayoutSpan:
    """Get the span of the rectangle."""
    return LayoutSpan(self.colSpan, self.rowSpan)

  @colSpan.SET
  @rowSpan.SET
  @topLeft.SET
  @topRight.SET
  @bottomRight.SET
  @bottomLeft.SET
  @span.SET
  def _badSet(self, *args) -> None:
    """Setter-function for the rectangle. """
    desc = getattr(type(self), self.__set_key__, )
    raise ReadOnlyError(self, desc, args[0])

  def __setattr__(self, key: str, value: Any) -> None:
    """Set the attribute of the rectangle."""
    self.__set_key__ = key
    return BaseObject.__setattr__(self, key, value)

  def __iter__(self, ) -> Self:
    """Iterate over the rectangle."""
    items = []
    for i in range(self.colSpan):
      for j in range(self.rowSpan):
        col = self.left + i
        row = self.top + j
        items.append(LayoutIndex(col, row))
    self.__iter_contents__ = items
    return self

  def __next__(self) -> LayoutIndex:
    """Get the next item in the rectangle."""
    if self.__iter_contents__:
      return self.__iter_contents__.pop(0)
    self.__iter_contents__ = None
    raise StopIteration

  def __len__(self, ) -> int:
    """Get the length of the rectangle."""
    return len(self.span)

  def __abs__(self, ) -> int:
    """Get the absolute value of the rectangle."""
    return abs(self.span)

  def __bool__(self, ) -> bool:
    """The rectangle containing only 0, 0 is Falsy"""
    if self.topLeft:
      return True
    if len(self) == 1:
      return False
    return True

  @overload(LayoutIndex)
  def __contains__(self, other: LayoutIndex) -> bool:
    """Check if the rectangle contains the item."""
    if other.row < self.top or other.row > self.bottom:
      return False
    if other.col < self.left or other.col > self.right:
      return False
    return True

  @overload(int, int)
  def __contains__(self, col: int, row: int) -> bool:
    """Check if the rectangle contains the item."""
    if row < self.top or row > self.bottom:
      return False
    if col < self.left or col > self.right:
      return False
    return True

  @overload(THIS)
  def __contains__(self, other: Self) -> bool:
    """Check if the rectangle contains the item."""
    if other.top < self.top or other.bottom > self.bottom:
      return False
    if other.left < self.left or other.right > self.right:
      return False
    return True

  #  topLeft, bottomRight

  @overload(THIS, THIS)  # bounding both rectangles
  def __init__(self, r0: Self, r1: Self) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
      assert isinstance(r0.left, int)
      assert isinstance(r1.left, int)
      assert isinstance(r0.top, int)
      assert isinstance(r1.top, int)
      assert isinstance(r0.right, int)
      assert isinstance(r1.right, int)
      assert isinstance(r0.bottom, int)
      assert isinstance(r1.bottom, int)

    L = min(r0.left, r1.left)
    T = min(r0.top, r1.top)
    R = max(r0.right, r1.right)
    B = max(r0.bottom, r1.bottom)

    self.__init__(L, T, R, B)

  @overload(THIS, LayoutIndex)  # bounding rectangle and index
  def __init__(self, r0: Self, r1: LayoutIndex) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
      assert isinstance(r0.left, int)
      assert isinstance(r1.col, int)
      assert isinstance(r0.top, int)
      assert isinstance(r1.row, int)
      assert isinstance(r0.right, int)
      assert isinstance(r0.bottom, int)

    L = min(r0.left, r1.col)
    T = min(r0.top, r1.row)
    R = max(r0.right, r1.col)
    B = max(r0.bottom, r1.row)
    self.__init__(L, T, R, B)

  @overload(THIS, int, int)
  def __init__(self, r0: Self, R: int, B: int) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    index = LayoutIndex(R, B)
    self.__init__(r0, index)

  @overload(int, int, int, int)
  def __init__(self, *args) -> None:
    L, T, R, B = args
    self.__left_col__ = L
    self.__top_row__ = T
    self.__right_col__ = R
    self.__bottom_row__ = B

  @overload(LayoutIndex, LayoutIndex)
  def __init__(self, *args) -> None:
    TL, BR = args
    self.__left_col__ = TL.col
    self.__top_row__ = TL.row
    self.__right_col__ = BR.col
    self.__bottom_row__ = BR.row

  @overload(LayoutIndex, int, int)
  def __init__(self, *args) -> None:
    TL, R, B = args
    self.__left_col__ = TL.col
    self.__top_row__ = TL.row
    self.__right_col__ = TL.col + R - 1
    self.__bottom_row__ = TL.row + B - 1

  @overload(int, int, LayoutIndex)
  def __init__(self, *args) -> None:
    L, T, BR = args
    self.__left_col__ = L
    self.__top_row__ = T
    self.__right_col__ = BR.col
    self.__bottom_row__ = BR.row

  #  topLeft, Span

  @overload(LayoutIndex, THIS)
  def __init__(self, *args) -> None:
    TL, SP = args
    self.__left_col__ = TL.col
    self.__top_row__ = TL.row
    self.__right_col__ = TL.col + SP.colSpan - 1
    self.__bottom_row__ = TL.row + SP.rowSpan - 1

  @overload(int, int, THIS)
  def __init__(self, *args) -> None:
    L, T, SP = args
    self.__left_col__ = L
    self.__top_row__ = T
    self.__right_col__ = L + SP.colSpan - 1
    self.__bottom_row__ = T + SP.rowSpan - 1

  @overload(LayoutIndex, LayoutSpan)
  def __init__(self, *args) -> None:
    TL, SP = args
    self.__left_col__ = TL.col
    self.__top_row__ = TL.row
    self.__right_col__ = TL.col + SP.colSpan - 1
    self.__bottom_row__ = TL.row + SP.rowSpan - 1

  @overload(int, int, LayoutSpan)
  def __init__(self, *args) -> None:
    L, T, SP = args
    self.__left_col__ = L
    self.__top_row__ = T
    self.__right_col__ = L + SP.colSpan - 1
    self.__bottom_row__ = T + SP.rowSpan - 1

  @overload(LayoutSpan)  # topLeft == LIndex(0, 0)
  def __init__(self, span: LayoutSpan) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(0, 0, span.nCols - 1, span.nRows - 1)

  #  topLeft, topLeft (spans == 1, 1)

  @overload(int, int)
  def __init__(self, *args) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(*args, *args)

  @overload(LayoutIndex)
  def __init__(self, index: LayoutIndex) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(index, index)

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(other.left, other.top, other.right, other.bottom)

  @overload()
  def __init__(self, *args) -> None:
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(0, 0, 0, 0)

  @classmethod
  def fromIndices(cls, *indices: LayoutIndex) -> Self:
    """Create a LayoutRect from a list of indices."""
    L = min([i.col for i in indices])
    T = min([i.row for i in indices])
    R = max([i.col for i in indices])
    B = max([i.row for i in indices])
    return cls(L, T, R, B)
