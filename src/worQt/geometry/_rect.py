"""Rect encapsulates rectangles in a 2D space."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect, QRectF
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from typing import TYPE_CHECKING

from worktoy.waitaminute import VariableNotNone, TypeException

from worQt.geometry import Size, Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator


class Rect(BaseObject):
  """Rect encapsulates rectangles in a 2D space."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_left__ = 0.0
  __fallback_top__ = 0.0
  __fallback_right__ = 1.0
  __fallback_bottom__ = 1.0

  #  Private Variables
  __left_edge__ = None
  __top_edge__ = None
  __right_edge__ = None
  __bottom_edge__ = None

  #  Public Variables
  left = Field()
  top = Field()
  right = Field()
  bottom = Field()

  #  Virtual Variables
  width = Field()  # Width of the rectangle (right - left)
  height = Field()  # Height of the rectangle (bottom - top)
  size = Field()  # Size of the rectangle (width, height)
  topLeft = Field()  # Top-left corner point of the rectangle
  topRight = Field()  # Top-right corner point of the rectangle
  bottomRight = Field()  # Bottom-right corner point of the rectangle
  bottomLeft = Field()  # Bottom-left corner point of the rectangle
  center = Field()  # Center point of the rectangle
  Q = Field()  # QPoint representation of the rectangle
  QF = Field()  # QPointF representation of the rectangle

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @left.GET
  def _getLeft(self, **kwargs) -> float:
    """Get the left edge of the rectangle."""
    if self.__left_edge__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__left_edge__ = self.__fallback_left__
      return self._getLeft(_recursion=True)
    return self.__left_edge__

  @top.GET
  def _getTop(self, **kwargs) -> float:
    """Get the top edge of the rectangle."""
    if self.__top_edge__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__top_edge__ = self.__fallback_top__
      return self._getTop(_recursion=True)
    return self.__top_edge__

  @right.GET
  def _getRight(self, **kwargs) -> float:
    """Get the right edge of the rectangle."""
    if self.__right_edge__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__right_edge__ = self.__fallback_right__
      return self._getRight(_recursion=True)
    return self.__right_edge__

  @bottom.GET
  def _getBottom(self, **kwargs) -> float:
    """Get the bottom edge of the rectangle."""
    if self.__bottom_edge__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__bottom_edge__ = self.__fallback_bottom__
      return self._getBottom(_recursion=True)
    return self.__bottom_edge__

  @width.GET
  def _getWidth(self, **kwargs) -> float:
    return self.right - self.left

  @height.GET
  def _getHeight(self, **kwargs) -> float:
    return self.bottom - self.top

  @size.GET
  def _getSize(self, **kwargs) -> Size:
    """Get the size of the rectangle as a tuple (width, height)."""
    return Size(self.width, self.height)

  @topLeft.GET
  def _getTopLeft(self, **kwargs) -> Point2D:
    """Get the top-left corner point of the rectangle."""
    return Point2D(self.left, self.top)

  @topRight.GET
  def _getTopRight(self, **kwargs) -> Point2D:
    """Get the top-right corner point of the rectangle."""
    return Point2D(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self, **kwargs) -> Point2D:
    """Get the bottom-right corner point of the rectangle."""
    return Point2D(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self, **kwargs) -> Point2D:
    """Get the bottom-left corner point of the rectangle."""
    return Point2D(self.left, self.bottom)

  @center.GET
  def _getCenter(self, **kwargs) -> Point2D:
    """Get the center point of the rectangle."""
    x = (self.left + self.right) / 2
    y = (self.top + self.bottom) / 2
    return Point2D(x, y)

  @QF.GET
  def _getQF(self, **kwargs) -> QRectF:
    """Get the QRectF representation of the rectangle."""
    return QRectF(self.left, self.top, self.width, self.height)

  @Q.GET
  def _getQ(self, **kwargs) -> QRect:
    return QRectF.toRect(self.QF, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @left.SET
  def _setLeft(self, value: float) -> None:
    """Set the left edge of the rectangle."""
    if self.__left_edge__ is not None:
      raise VariableNotNone('left', self.__left_edge__, )
    if isinstance(value, (int, float)):
      self.__left_edge__ = value
    else:
      raise TypeException('value', value, int, float, )

  @top.SET
  def _setTop(self, value: float) -> None:
    """Set the top edge of the rectangle."""
    if self.__top_edge__ is not None:
      raise VariableNotNone('top', self.__top_edge__, )
    if isinstance(value, (int, float)):
      self.__top_edge__ = value
    else:
      raise TypeException('value', value, int, float, )

  @right.SET
  def _setRight(self, value: float) -> None:
    """Set the right edge of the rectangle."""
    if self.__right_edge__ is not None:
      raise VariableNotNone('right', self.__right_edge__, )
    if isinstance(value, (int, float)):
      self.__right_edge__ = value
    else:
      raise TypeException('value', value, int, float, )

  @bottom.SET
  def _setBottom(self, value: float) -> None:
    """Set the bottom edge of the rectangle."""
    if self.__bottom_edge__ is not None:
      raise VariableNotNone('bottom', self.__bottom_edge__, )
    if isinstance(value, (int, float)):
      self.__bottom_edge__ = value
    else:
      raise TypeException('value', value, int, float, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    """Check if the rectangle is valid."""
    return True if self.width ** 2 * self.height ** 2 > 1e-12 else False

  def __contains__(self, item: Any, **kwargs) -> bool:
    """Check if a point is inside the rectangle."""
    if isinstance(item, Point2D):
      if self.left < item.x < self.right:
        if self.top < item.y < self.bottom:
          return True
      return False
    if kwargs.get('_recursion', False):
      raise RecursionError
    other = Point2D.__add__(Point2D(0, 0), item, )
    if other is NotImplemented:
      return NotImplemented
    return self.__contains__(other, _recursion=True)
