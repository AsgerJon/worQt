"""
Rect is a plane rectangle defined by integer 'left', 'top', 'right' and
'bottom', with the usual derived geometry ('width', 'height', 'size',
corners, 'center') and Qt conversions ('Q' -> 'QRect', 'QF' -> 'QRectF'). A
'BaseObject' with overloaded constructors: four edges, two corner points, a
top-left point and a size, a 'QRect'/'QRectF' (strict), a bare size at the
origin, or another rect.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF, QPoint, QSize
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ._point_2d import Point2D
from ._size import Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class Rect(BaseObject):
  """A rectangle defined by integer left/top/right/bottom edges."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  left = AttriBox[int](0)
  top = AttriBox[int](0)
  right = AttriBox[int](0)
  bottom = AttriBox[int](0)

  #  Virtual Variables
  width: Field[int] = Field()
  height: Field[int] = Field()
  size: Field[Size] = Field()
  topLeft: Field[Point2D] = Field()
  topRight: Field[Point2D] = Field()
  bottomRight: Field[Point2D] = Field()
  bottomLeft: Field[Point2D] = Field()
  center: Field[Point2D] = Field()
  Q: Field[QRect] = Field()
  QF: Field[QRectF] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @width.GET
  def _getWidth(self) -> int:
    return self.right - self.left

  @height.GET
  def _getHeight(self) -> int:
    return self.bottom - self.top

  @size.GET
  def _getSize(self) -> Size:
    return Size(self.width, self.height)

  @topLeft.GET
  def _getTopLeft(self) -> Point2D:
    return Point2D(self.left, self.top)

  @topRight.GET
  def _getTopRight(self) -> Point2D:
    return Point2D(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self) -> Point2D:
    return Point2D(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self) -> Point2D:
    return Point2D(self.left, self.bottom)

  @center.GET
  def _getCenter(self) -> Point2D:
    return Point2D(self.left + self.width // 2, self.top + self.height // 2)

  @Q.GET
  def _getQRect(self) -> QRect:
    return QRect(QPoint(self.left, self.top), QSize(self.width, self.height))

  @QF.GET
  def _getQRectF(self) -> QRectF:
    return QRectF(self.Q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, left: int, top: int, right: int, bottom: int) -> None:
    self.left, self.top, self.right, self.bottom = left, top, right, bottom

  @overload(Point2D, Point2D)
  def __init__(self, topLeft: Point2D, bottomRight: Point2D) -> None:
    self.left, self.top = topLeft.x, topLeft.y
    self.right, self.bottom = bottomRight.x, bottomRight.y

  @overload(Point2D, Size)
  def __init__(self, topLeft: Point2D, size: Size) -> None:
    self.left, self.top = topLeft.x, topLeft.y
    self.right = topLeft.x + size.width
    self.bottom = topLeft.y + size.height

  @overload(Size)
  def __init__(self, size: Size) -> None:
    self.right, self.bottom = size.width, size.height

  @overload(QRect, strict=True)
  def __init__(self, rect: QRect) -> None:
    self.left, self.top = rect.x(), rect.y()
    self.right = rect.x() + rect.width()
    self.bottom = rect.y() + rect.height()

  @overload(QRectF, strict=True)
  def __init__(self, rect: QRectF) -> None:
    self.left, self.top = round(rect.left()), round(rect.top())
    self.right, self.bottom = round(rect.right()), round(rect.bottom())

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.left, self.top = other.left, other.top
    self.right, self.bottom = other.right, other.bottom

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D)
  def __contains__(self, point: Point2D) -> bool:
    if self.left <= point.x <= self.right:
      return True if self.top <= point.y <= self.bottom else False
    return False

  @overload(THIS)
  def __contains__(self, other: Self) -> bool:
    if other.topLeft in self:
      return True if other.bottomRight in self else False
    return False

  def __str__(self) -> str:
    return 'Rect(%d, %d, %d, %d)' % (
        self.left, self.top, self.right, self.bottom)

  __repr__ = __str__
