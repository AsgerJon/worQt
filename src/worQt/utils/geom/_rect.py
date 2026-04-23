"""
Rect subclasses EuclideanObject and encapsulates a plane rectangle.
Instances are defined by left, top, right and bottom. Instances also
exposes various other properties which are derived from these four.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import (QRect, QRectF, QPoint, QPointF, QLine, QLineF,
  QSize, QSizeF)
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload

from .. import Eps
from .euclid import EuclideanObject, Dimension
from . import Size, Point2D, Segment, Line

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias, Union
  import typing
  from . import InSets

  Point: TypeAlias = Union[Point2D, Field]
  SizeField: TypeAlias = Union[Size, Field]
  QField: TypeAlias = Union[QRect, Field]
  QFField: TypeAlias = Union[QRectF, Field]
  LineField: TypeAlias = Union[Line, Field]
  SegField: TypeAlias = Union[Segment, Field]
  Int: TypeAlias = Union[int, Field]
  QSizes: TypeAlias = Union[QSize, QSizeF]


class Rect(EuclideanObject):
  """
  Rect subclasses EuclideanObject and encapsulates a plane rectangle.
  Instances are defined by left, top, right and bottom. Instances also
  exposes various other properties which are derived from these four.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()

  #  Public Variables
  left = Dimension(int, 0, 'l', 'lt', 'x1')
  top = Dimension(int, 0, 't', 'tp', 'y1')
  right = Dimension(int, 0, 'r', 'rt', 'x2')
  bottom = Dimension(int, 0, 'b', 'bm', 'y2')

  #  Virtual Variables
  width: Int = Field()
  height: Int = Field()
  size: SizeField = Field()  # Size object
  topLeft: Point = Field()  # Point2D object
  topRight: Point = Field()  # Point2D object
  bottomRight: Point = Field()  # Point2D object
  bottomLeft: Point = Field()  # Point2D object
  center: Point = Field()  # Point2D object
  Q: QField = Field()  # QRect object
  QF: QFField = Field()  # QRectF object
  topLine: SegField = Field()  # The line segment spanning the top edge
  rightLine: SegField = Field()  # The line segment spanning the right edge
  bottomLine: SegField = Field()  # The line segment spanning the bottom edge
  leftLine: SegField = Field()  # The line segment spanning the left edge

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @width.GET
  def _getWidth(self, ) -> int:
    return self.right - self.left

  @height.GET
  def _getHeight(self, ) -> int:
    return self.bottom - self.top

  @size.GET
  def _getSize(self, ) -> Size:
    return Size(self.width, self.height)

  @topLeft.GET
  def _getTopLeft(self, ) -> Point2D:
    return Point2D(self.left, self.top)

  @topRight.GET
  def _getTopRight(self, ) -> Point2D:
    return Point2D(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self, ) -> Point2D:
    return Point2D(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self, ) -> Point2D:
    return Point2D(self.left, self.bottom)

  @center.GET
  def _getCenter(self, ) -> Point2D:
    return Point2D(self.left + self.width / 2, self.top + self.height / 2)

  @Q.GET
  def _getQRect(self, ) -> QRect:
    topLeft = QPoint(self.left, self.top)
    size = QSize(self.width, self.height)
    return QRect(topLeft, size)

  @QF.GET
  def _getQRectF(self, ) -> QRectF:
    return QRect.toRectF(self.Q)

  @topLine.GET
  def _getTopLine(self, ) -> Segment:
    return Segment(self.topLeft, self.topRight)

  @rightLine.GET
  def _getRightLine(self, ) -> Segment:
    return Segment(self.topRight, self.bottomRight)

  @bottomLine.GET
  def _getBottomLine(self, ) -> Segment:
    return Segment(self.bottomRight, self.bottomLeft)

  @leftLine.GET
  def _getLeftLine(self, ) -> Segment:
    return Segment(self.bottomLeft, self.topLeft)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D)
  def __contains__(self, point: Point2D) -> bool:
    if self.left <= point.x <= self.right:
      if self.top <= point.y <= self.bottom:
        return True
    return False

  @overload(QPoint)
  def __contains__(self, point: QPoint) -> bool:
    return True if Point2D(point) in self else False

  @overload(QPointF)
  def __contains__(self, point: QPointF) -> bool:
    return True if Point2D(point) in self else False

  @overload(QRect)
  def __contains__(self, rect: QRect) -> bool:
    if QRect.isNull(rect, ):
      return True  # Set semantic, the empty set is a subset of every set
    if rect.topLeft() in self:
      if rect.bottomRight() in self:
        return True
    return False

  @overload(QRectF)
  def __contains__(self, rect: QRectF) -> bool:
    return True if QRectF.toRect(rect, ) in self else False

  @overload(QLine)
  def __contains__(self, line: QLine) -> bool:
    if line.p1() in self:
      if line.p2() in self:
        return True
    return False

  @overload(QLineF)
  def __contains__(self, line: QLineF) -> bool:
    return True if QLineF.toLine(line, ) in self else False

  @overload(Segment)
  def __contains__(self, segment: Segment) -> bool:
    if segment.P in self:
      if segment.Q in self:
        return True
    return False

  @overload(THIS)
  def __contains__(self, other: Self) -> bool:
    if other.topLeft in self:
      if other.bottomRight in self:
        return True
    return False

  @overload(Point2D)
  def __add__(self, other: Point2D) -> Self:
    """
    This method creates a new Rect of same size as 'self', but translated
    by the given point.
    """
    newLeft = self.left + other.x
    newTop = self.top + other.y
    newRight = self.right + other.x
    newBottom = self.bottom + other.y
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(THIS)
  def __add__(self, other: Self) -> Self:
    """
    Adding two rects creates a new 'Rect' shaped such as to exactly
    contain both 'self' and 'other'. The union of the two rects. For
    intersection, use multiplication operator.
    """
    newLeft = min(self.left, other.left)
    newTop = min(self.top, other.top)
    newRight = max(self.right, other.right)
    newBottom = max(self.bottom, other.bottom)
    return Rect(newLeft, newTop, newRight, newBottom)

  @overload(THIS)
  def __mul__(self, other: Self) -> Self:
    """
    Multiplying two rects creates a new 'Rect' shaped such as to be exactly
    contained by both 'self' and 'other'. The intersection of the two rects.
    For union, use addition operator.
    """
    newLeft = max(self.left, other.left)
    newTop = max(self.top, other.top)
    newRight = min(self.right, other.right)
    newBottom = min(self.bottom, other.bottom)
    cls = type(self)
    newRect = cls(newLeft, newTop, newRight, newBottom)
    if newLeft > newRight or newTop > newBottom:
      return cls(newRect.center, Size(0, 0))
    return newRect

  @overload(Point2D)
  def __radd__(self, other: Point2D) -> Self:
    return self + other

  @overload(Point2D)
  def __sub__(self, other: Point2D) -> Self:
    """
    This method creates a new Rect of same size as 'self', but translated
    by the negative of the given point.
    """
    return self + (-other)

  if TYPE_CHECKING:  # pragma: no cover
    #  Shown here for informational purposes. Because 'InSets' depends
    #  upon 'Rect', these are *actually* implemented in 'InSets' at the
    #  '__radd__' and '__rsub__' methods respectively.
    @overload
    def __add__(self, other: InSets) -> Self: ...

    @overload
    def __sub__(self, other: InSets) -> Self: ...

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D, Point2D)  # topLeft, bottomRight
  def __init__(self, topLeft: Point2D, bottomRight: Point2D, **kw) -> None:
    self.left, self.top = topLeft
    self.right, self.bottom = bottomRight
    if kw:
      self.__init__(**kw)

  @overload.flex(Point2D, Size)  # topLeft, size
  def __init__(self, topLeft: Point2D, size: Size, **kw) -> None:
    bottom, right = topLeft.x + size.width, topLeft.y + size.height
    self.__init__(topLeft, Point2D(bottom, right), **kw)

  @overload.flex(THIS, Size)  # THIS.center with given size
  def __init__(self, other: Self, size: Size, **kw) -> None:
    top = int(round(other.center.y - size.height / 2))
    left = int(round(other.center.x - size.width / 2))
    topLeft = Point2D(left, top)
    self.__init__(topLeft, size, **kw)

  @overload(QRect, strict=True)
  def __init__(self, qRect: QRect, **kw) -> None:
    topLeft = Point2D(qRect.topLeft())
    size = Size(qRect.size())
    self.__init__(topLeft, size, **kw)

  @overload(QRectF, strict=True)
  def __init__(self, qRectF: QRectF, **kw) -> None:
    self.__init__(QRectF.toRect(qRectF, ), **kw)

  @overload(Size)
  def __init__(self, size: Size, **kw) -> None:
    self.__init__(Point2D(0, 0), size, **kw)

  @overload(QSize, strict=True)
  @overload(QSizeF, strict=True)
  def __init__(self, qSize: QSizes, **kw) -> None:
    self.__init__(Size(qSize), **kw)
