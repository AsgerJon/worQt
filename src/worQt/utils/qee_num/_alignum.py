"""
Alignum enumerates alignment options.
"""
#  Apache-2.0 license
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
    raise ValueError  # pragma: no cover

  @horizontal.GET
  def _getHorizontal(self, ) -> HAlignum:
    for h in HAlignum:
      if self.value & h.value:
        return h
    raise ValueError  # pragma: no cover

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def apply(self, static: Any, moving: Any) -> Rect:
    """
    Align 'moving' (a rect or size) within 'static' (a rect or size),
    returning the placed 'Rect'. Plain method, not overloaded: an
    overloaded method cannot be called on a frozen 'KeeNum' member.
    """
    staticRect = self._toRect(static)
    movingRect = self._toRect(moving)
    movingRect = self._applyHorizontal(staticRect, movingRect)
    return self._applyVertical(staticRect, movingRect)

  @staticmethod
  def _toRect(obj: Any) -> Rect:
    """Normalize a rect/size (worQt or Qt) to a 'Rect'."""
    if isinstance(obj, Rect):
      return obj
    if isinstance(obj, (Size, QSize, QSizeF)):
      return Rect(Size(obj))
    return Rect(obj)  # QRect / QRectF

  def _applyHorizontal(self, staticRect: Rect, movingRect: Rect) -> Rect:
    top, bottom = movingRect.top, movingRect.bottom
    if self.horizontal is HAlignum.LEFT:
      left = staticRect.left
    elif self.horizontal is HAlignum.CENTER:
      left = int(round(staticRect.center.x - movingRect.width / 2))
    elif self.horizontal is HAlignum.RIGHT:
      left = staticRect.right - movingRect.width
    else:  # pragma: no cover
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
    else:  # pragma: no cover
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
    raise ValueError  # pragma: no cover
