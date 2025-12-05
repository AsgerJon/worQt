"""
Rect encapsulates rectangles.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF, QSize, QSizeF
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities import maybe, textFmt

from moreworktoy.desc import Alias

from . import FourDim, Point, Size
from ...nums import Alignum
from ...nums import HorizontalAlignum as H
from ...nums import VerticalAlignum as V

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Self


class Rect(FourDim):
  """
  Rect encapsulates rectangles.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __left_keys__ = 'left', 'Left', 'l', 'L', 'x0', 'X0'
  __top_keys__ = 'top', 'Top', 't', 'T', 'y0', 'Y0'
  __right_keys__ = 'right', 'Right', 'r', 'R', 'x1', 'X1'
  __bottom_keys__ = 'bottom', 'Bottom', 'b', 'B', 'y1', 'Y1'
  __width_keys__ = 'width', 'Width', 'w', 'W'
  __height_keys__ = 'height', 'Height', 'h', 'H'

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  left = Alias('v0')
  top = Alias('v1')
  right = Alias('v2')
  bottom = Alias('v3')

  #  Virtual Variables
  topLeft = Field()
  topRight = Field()
  bottomRight = Field()
  bottomLeft = Field()
  corners = Field()
  center = Field()
  width = Field()
  height = Field()
  size = Field()
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @topLeft.GET
  def _getTopLeft(self, ) -> Point:
    return Point(self.left, self.top)

  @topRight.GET
  def _getTopRight(self, ) -> Point:
    return Point(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self, ) -> Point:
    return Point(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self, ) -> Point:
    return Point(self.left, self.bottom)

  @corners.GET
  def _getCorners(self, ) -> Iterator[Point]:
    yield self.topLeft
    yield self.topRight
    yield self.bottomRight
    yield self.bottomLeft

  @center.GET
  def _getCenter(self, ) -> Point:
    x = self.left / 2 + self.right / 2
    y = self.top / 2 + self.bottom / 2
    out = Point()
    out.__dim_values__ = x, y
    return out

  @size.GET
  def _getSize(self, ) -> Size:
    w = self.right - self.left
    h = self.bottom - self.top
    out = Size()
    out.__dim_values__ = w, h
    return out

  @width.GET
  def _getWidth(self, ) -> int:
    return self.size.width

  @height.GET
  def _getHeight(self, ) -> int:
    return self.size.height

  @Q.GET
  def _getQ(self, ) -> QRect:
    return QRect(self.left, self.top, self.width, self.height)

  @QF.GET
  def _getQF(self, ) -> QRectF:
    return QRect.toRectF(self.Q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __contains__(self, item: Any) -> bool:
    if isinstance(item, Point):
      if self.left <= item.x <= self.right:
        if self.top <= item.y <= self.bottom:
          return True
      return False
    cls = type(self)
    if isinstance(item, cls):
      for corner in item.corners:
        if corner not in self:
          return False
      return True
    other = self._resolveOther(item)
    if other is NotImplemented:
      try:
        other = Point(other)
      except (TypeError, ValueError):
        return False
    return other in self

  def __bool__(self, ) -> bool:
    return True if self.size else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point, Point)
  def __init__(self, topLeft: Point, bottomRight: Point) -> None:
    intArgs = []
    for x, y in zip(topLeft, bottomRight):
      intArgs.append(int(x))
      intArgs.append(int(y))
    FourDim.__init__(self, *intArgs)

  @overload(Point, Size)
  def __init__(self, topLeft: Point, size: Size) -> None:
    left = topLeft.x
    top = topLeft.y
    right = left + size.width
    bottom = top + size.height
    FourDim.__init__(self, left, top, right, bottom)

  @overload(Size, Point)
  def __init__(self, size: Size, bottomRight: Point) -> None:
    right = bottomRight.x
    bottom = bottomRight.y
    left = right - size.width
    top = bottom - size.height
    FourDim.__init__(self, left, top, right, bottom)

  @overload(int, int)
  def __init__(self, width: int, height: int) -> None:
    FourDim.__init__(self, 0, 0, width, height)

  @overload(Point)
  def __init__(self, point: Point) -> None:
    self.__init__(point, point)

  @overload(Size)
  def __init__(self, size: Size) -> None:
    self.__init__(Point(), size)

  @overload(QRect)
  def __init__(self, qRect: QRect) -> None:
    left = qRect.left()
    top = qRect.top()
    right = qRect.right()
    bottom = qRect.bottom()
    FourDim.__init__(self, left, top, right, bottom)

  @overload(QRectF)
  def __init__(self, qRectF: QRectF) -> None:
    self.__init__(QRectF.toRect(qRectF))

  @overload(QSize)
  def __init__(self, qSize: QSize) -> None:
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def alignInner(self, target: Self, alignFlag: Alignum) -> Self:
    """
    Creates a new 'Rect' object having the same size as 'self' but aligned
    within 'target' according to the alignment setting of 'target'.
    """
    cls = type(self)
    target = cls(target)
    if TYPE_CHECKING:  # pragma: no cover
      assert isinstance(target.left, int)
      assert isinstance(target.top, int)
      assert isinstance(target.right, int)
      assert isinstance(target.bottom, int)
      assert isinstance(target.width, int)
      assert isinstance(target.height, int)
      assert isinstance(target.center, Point)

    newSize = self.size.scaleInner(target.size)
    left, top, right, bottom = None, None, None, None
    if alignFlag.horizontal == H.LEFT:
      left = target.left
      right = left + newSize.width
    elif alignFlag.horizontal == H.CENTER:
      left = int(target.center.x - newSize.width / 2)
      right = int(target.center.x + newSize.width / 2)
    elif alignFlag.horizontal == H.RIGHT:
      right = target.right
      left = right - newSize.width
    else:
      infoSpec = """Unknown horizontal alignment value: '%s'!"""
      info = infoSpec % (alignFlag.horizontal,)
      raise ValueError(textFmt(info))
    if alignFlag.vertical == V.TOP:
      top = target.top
      bottom = top + newSize.height
    elif alignFlag.vertical == V.CENTER:
      top = int(target.center.y - newSize.height / 2)
      bottom = int(target.center.y + newSize.height / 2)
    elif alignFlag.vertical == V.BOTTOM:
      bottom = target.bottom
      top = bottom - newSize.height
    else:
      infoSpec = """Unknown vertical alignment value: '%s'!"""
      info = infoSpec % (alignFlag.vertical,)
      raise ValueError(textFmt(info))
    out = cls()
    out.__dim_values__ = left, top, right, bottom
    return out

  def alignOuter(self, target: Self, alignFlag: Alignum) -> Self:
    return target.alignInner(self, alignFlag)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _resolveKey(self, key: str) -> int:
    if key in self.__left_keys__:
      return self.left
    if key in self.__top_keys__:
      return self.top
    if key in self.__right_keys__:
      return self.right
    if key in self.__bottom_keys__:
      return self.bottom
    if key in self.__width_keys__:
      return self.width
    if key in self.__height_keys__:
      return self.height
    return FourDim._resolveKey(self, key)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
