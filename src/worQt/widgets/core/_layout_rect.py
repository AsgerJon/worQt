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
from worQt.widgets.core import LayoutIndex, LayoutSpan

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

  @colSpan.GET
  def _getColSpan(self) -> int:
    """Get the column span."""
    return self.right - self.left + 1

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
    try:
      out: LayoutIndex = self.__iter_contents__.pop(0)
      if isinstance(out, LayoutIndex):
        return out
    except IndexError:
      raise StopIteration
    finally:
      if not self.__iter_contents__:
        self.__iter_contents__ = None

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
