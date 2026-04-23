"""
Alignum enumerates alignment options.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QSize, QRect, QRectF, QSizeF
from icecream import ic
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.keenum import KeeNum, Kee

from . import VAlignum, HAlignum
from ..geom import Rect, Size, Point2D

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

QTop = Qt.AlignmentFlag.AlignTop
QVCenter = Qt.AlignmentFlag.AlignVCenter
QBottom = Qt.AlignmentFlag.AlignBottom

QLeft = Qt.AlignmentFlag.AlignLeft
QHCenter = Qt.AlignmentFlag.AlignHCenter
QRight = Qt.AlignmentFlag.AlignRight

QCenter = Qt.AlignmentFlag.AlignCenter


class Alignum(KeeNum):
  """
  Alignum enumerates alignment options.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables

  #  Virtual Variables

  #  Enumerations
  TOP_LEFT = Kee[Qt.AlignmentFlag](QTop | QLeft)
  TOP_CENTER = Kee[Qt.AlignmentFlag](QTop | QHCenter)
  TOP_RIGHT = Kee[Qt.AlignmentFlag](QTop | QRight)

  CENTER_LEFT = Kee[Qt.AlignmentFlag](QVCenter | QLeft)
  CENTER = Kee[Qt.AlignmentFlag](QCenter)
  CENTER_RIGHT = Kee[Qt.AlignmentFlag](QVCenter | QRight)

  BOTTOM_LEFT = Kee[Qt.AlignmentFlag](QBottom | QLeft)
  BOTTOM_CENTER = Kee[Qt.AlignmentFlag](QBottom | QHCenter)
  BOTTOM_RIGHT = Kee[Qt.AlignmentFlag](QBottom | QRight)

  #  Virtual Variables
  Q = Field()
  vertical = Field()
  horizontal = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self, ) -> Qt.AlignmentFlag:
    return self.value

  @vertical.GET
  def _getVertical(self, ) -> VAlignum:
    for v in VAlignum:
      if self.value & v.value:
        return v
    raise ValueError

  @horizontal.GET
  def _getHorizontal(self, ) -> HAlignum:
    for h in HAlignum:
      if self.value & h.value:
        return h
    raise ValueError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Rect, Rect)
  def apply(self, staticRect: Rect, movingRect: Rect) -> Rect:
    """
    Applies the alignment to the given rectangles.

    Args:
      staticRect: The rectangle to align to.
      movingRect: The rectangle to be aligned.

    Returns:
      The aligned rectangle.
    """
    movingRect = self._applyHorizontal(staticRect, movingRect)
    return self._applyVertical(staticRect, movingRect)

  @overload(Size, Size)
  def apply(self, staticSize: Size, movingSize: Size) -> Rect:
    staticRect = Rect(Point2D(0, 0), staticSize)
    movingRect = Rect(Point2D(0, 0), movingSize)
    return self.apply(staticRect, movingRect)

  @overload(Size, Rect)
  def apply(self, staticSize: Size, movingRect: Rect) -> Rect:
    staticRect = Rect(Point2D(0, 0), staticSize)
    return self.apply(staticRect, movingRect)

  @overload(Rect, Size)
  def apply(self, staticRect: Rect, movingSize: Size) -> Rect:
    movingRect = Rect(Point2D(0, 0), movingSize)
    return self.apply(staticRect, movingRect)

  @overload(QRect, QSize, strict=True)
  @overload(QRectF, QSize, strict=True)
  @overload(QRect, QSizeF, strict=True)
  @overload(QRectF, QSizeF, strict=True)
  def apply(self, staticQRect: QRect, movingQSize: QSize) -> Rect:
    staticRect = Rect(staticQRect)
    movingRect = Rect(movingQSize)
    return self.apply(staticRect, movingRect)

  def _applyHorizontal(self, staticRect: Rect, movingRect: Rect) -> Rect:
    top, bottom = movingRect.top, movingRect.bottom
    if self.horizontal is HAlignum.LEFT:
      left = staticRect.left
    elif self.horizontal is HAlignum.CENTER:
      left = int(round(staticRect.center.x - movingRect.width / 2))
    elif self.horizontal is HAlignum.RIGHT:
      left = staticRect.right - movingRect.width
    else:
      raise ValueError
    return Rect(Point2D(left, top), movingRect.size)

  def _applyVertical(self, staticRect: Rect, movingRect: Rect) -> Rect:
    left, right = movingRect.left, movingRect.right
    if self.vertical is VAlignum.TOP:
      top = staticRect.top
    elif self.vertical is VAlignum.CENTER:
      top = int(round(staticRect.center.y - movingRect.height / 2))
    elif self.vertical is VAlignum.BOTTOM:
      top = staticRect.bottom - movingRect.height
    else:
      raise ValueError
    return Rect(Point2D(left, top), movingRect.size)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def combine(cls, vertical: VAlignum, horizontal: HAlignum) -> Alignum:
    alignum = None
    if isinstance(vertical, HAlignum) and isinstance(horizontal, VAlignum):
      return cls.combine(horizontal, vertical)
    hName, vName = horizontal.name, vertical.name
    for alignum in cls:
      if alignum.vertical is vertical and alignum.horizontal is horizontal:
        return alignum
    raise ValueError
