"""Rect encapsulates rectangles in a 2D space."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, QPoint, QPointF, QSize, QSizeF
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import VariableNotNone, TypeException
from worktoy.waitaminute.dispatch import DispatchException

from . import Size, Point2D, Margins

from typing import TYPE_CHECKING

from ..nums import Alignum
from ..nums import HorizontalAlignum as H
from ..nums import VerticalAlignum as V

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Self


class Rect(BaseObject):
  """Rect encapsulates rectangles in a 2D space."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_left__ = 0.0
  __fallback_top__ = 0.0
  __fallback_right__ = 0.0
  __fallback_bottom__ = 0.0

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
  diagonal = Field()  # Diagonal length of the rectangle
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

  @diagonal.GET
  def _getDiagonal(self, **kwargs) -> float:
    """Get the diagonal length of the rectangle."""
    return (self.width ** 2 + self.height ** 2) ** 0.5

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
    return QRect(self.left, self.top, self.width, self.height)

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

  def __contains__(self, other: Any, **kwargs) -> bool:
    """Check if a point is inside the rectangle."""
    cls = type(self)
    if isinstance(other, cls):
      if self.left > other.left:
        return False
      if self.top > other.top:
        return False
      if self.right < other.right:
        return False
      if self.bottom < other.bottom:
        return False
      return True
    if kwargs.get('_recursion', False):
      raise RecursionError
    try:
      other = cls(other, )
    except DispatchException:
      return NotImplemented
    else:
      return self.__contains__(other, _recursion=True)

  def __add__(self, other: Margins) -> Self:
    if isinstance(other, Margins):
      return Rect(
          self.left - other.left,
          self.top - other.top,
          self.right + other.right,
          self.bottom + other.bottom
      )
    try:
      other = Margins(other, )
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return self + other

  def __sub__(self, other: Margins) -> Self:
    """Subtract margins from the rectangle."""
    if isinstance(other, Margins):
      return Rect(
          self.left + other.left,
          self.top + other.top,
          self.right - other.right,
          self.bottom - other.bottom
      )
    try:
      other = Margins(other, )
    except (TypeError, ValueError):
      return NotImplemented
    else:
      return self - other

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS, Alignum)
  def align(self, other: Self, alignum: Alignum) -> Self:
    """
    Moves this rectangle to align with 'other' rectangle as specified
    by the alignment specified by the 'alignum' parameter.
    """
    cls = type(self)
    if alignum.horizontal is H.LEFT:
      left = other.left
    elif alignum.horizontal is H.CENTER:
      if TYPE_CHECKING:
        assert isinstance(other.left, float)
      left = other.left + (other.width - self.width) / 2
    elif alignum.horizontal is H.RIGHT:
      left = other.right - self.width
    else:
      name, value = 'alignum', alignum.horizontal
      raise TypeException(name, value, Alignum)
    if alignum.vertical is V.TOP:
      top = other.top
    elif alignum.vertical is V.CENTER:
      if TYPE_CHECKING:
        assert isinstance(other.top, float)
      top = other.top + (other.height - self.height) / 2
    elif alignum.vertical is V.BOTTOM:
      top = other.bottom - self.height
    else:
      name, value = 'alignum', alignum.vertical
      raise TypeException(name, value, Alignum)
    return cls(left, top, left + self.width, top + self.height)

  @overload(Alignum, THIS)
  def align(self, alignum: Alignum, other: Self) -> Self:
    return self.align(other, alignum)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(float, float, float, float)
  @overload(int, int, int, int)
  def __init__(self, *args) -> None:
    """Initialize the rectangle with left, top, right, bottom edges."""
    left, top, right, bottom = args
    self.__left_edge__ = float(min(left, right))
    self.__top_edge__ = float(min(top, bottom))
    self.__right_edge__ = float(max(left, right))
    self.__bottom_edge__ = float(max(top, bottom))

  @overload(Point2D, Point2D)
  def __init__(self, p: Point2D, q: Point2D) -> None:
    self.__init__(p.x, p.y, q.x, q.y)

  @overload(Point2D, Size)
  def __init__(self, p: Point2D, size: Size) -> None:
    left = int(p.x)
    top = int(p.y)
    right = int(left + size.width)
    bottom = int(top + size.height)
    self.__init__(left, top, right, bottom)

  @overload(Size, Point2D)
  def __init__(self, size: Size, p: Point2D) -> None:
    """Initialize the rectangle with a size and a point."""
    self.__init__(p, size)

  @overload(Size)
  def __init__(self, size: Size) -> None:
    """Initialize the rectangle with a size."""
    self.__init__(0, 0, size.width, size.height)

  @overload(QSize)
  @overload(QSizeF)
  def __init__(self, size: Union[QSize, QSizeF]) -> None:
    self.__init__(0, 0, int(size.width()), int(size.height()))

  @overload(QPointF, QPointF)
  @overload(QPoint, QPoint)
  def __init__(self, p: QPoint, q: QPoint) -> None:
    self.__init__(Point2D(p), Point2D(q), )

  @overload(QPoint, QSize)
  @overload(QPointF, QSize)
  @overload(QPoint, QSizeF)
  @overload(QPointF, QSizeF)
  def __init__(self, p: QPoint, size: QSize) -> None:
    self.__init__(Point2D(p), Size(size))

  @overload(QSize, QPoint)
  @overload(QSize, QPointF)
  @overload(QSizeF, QPoint)
  @overload(QSizeF, QPointF)
  def __init__(self, size: QSize, p: QPoint) -> None:
    """Initialize the rectangle with a size and a point."""
    self.__init__(p, size)

  @overload(QRect, )
  @overload(QRectF, )
  def __init__(self, rect: Union[QRect, QRectF]) -> None:
    """Initialize the rectangle from a QRect or QRectF."""
    self.__init__(rect.left(), rect.top(), rect.right(), rect.bottom())

  @overload(Point2D)
  def __init__(self, point: Point2D) -> None:
    """Creates a rectangle with no width or height at the given point. """
    self.__init__(point.x, point.y, point.x, point.y)

  @overload(QPoint)
  @overload(QPointF)
  def __init__(self, point: Union[QPoint, QPointF]) -> None:
    self.__init__(Point2D(point))

  @overload()
  def __init__(self, ) -> None:
    pass  # Using fallback values
