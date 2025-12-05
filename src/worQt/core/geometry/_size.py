"""
Size encapsulates rectangular sizes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QSize, QSizeF, QRect, QRectF

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt

from moreworktoy.desc import Alias

from . import TwoDim, Point

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Callable, Iterator


class Size(TwoDim):
  """
  Size encapsulates rectangular sizes.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __width_keys__ = 'width', 'Width', 'w', 'W'
  __height_keys__ = 'height', 'Height', 'h', 'H'

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  width = Alias('v0')
  height = Alias('v1')

  #  Virtual Variables
  area = Field()
  aspect = Field()
  q = Field()
  qF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @area.GET
  def _getArea(self, **kwargs) -> int:
    return self.width * self.height

  @aspect.GET
  def _getAspect(self, **kwargs) -> float:
    if self.height:
      if self.width:
        return self.width / self.height
      return .0
    raise ZeroDivisionError

  @q.GET
  def _getQ(self, ) -> QSize:
    return QSize(self.width, self.height)

  @qF.GET
  def _getQF(self, ) -> QSizeF:
    return QSize.toSizeF(self.q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __bool__(self, ) -> bool:
    return True if self.area > 1e-03 else False

  def __str__(self, ) -> str:
    infoSpec = """%s object of width: %d and height: %d"""
    clsName = type(self).__name__
    return textFmt(infoSpec % (clsName, self.width, self.height))

  def __repr__(self) -> str:
    infoSpec = """%s(%d, %d)"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, self.width, self.height)
    return textFmt(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, width: int, height: int) -> None:
    self.__dim_values__ = width, height

  @overload(Point, Point)
  def __init__(self, topLeft: Point, bottomRight: Point) -> None:
    width = abs(bottomRight.x - topLeft.x)
    height = abs(bottomRight.y - topLeft.y)
    self.__dim_values__ = width, height

  @overload(QSize)
  def __init__(self, qSize: QSize) -> None:
    self.__dim_values__ = qSize.width(), qSize.height()

  @overload(QSizeF)
  def __init__(self, qSizeF: QSizeF) -> None:
    self.__init__(QSizeF.toSize(qSizeF))

  @overload(QRect)
  def __init__(self, qRect: QRect) -> None:
    self.__init__(QRect.size(qRect))

  @overload(QRectF)
  def __init__(self, qRectF: QRectF) -> None:
    self.__init__(QRectF.toRect(qRectF))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def scaleInner(self, target: Self) -> Self:
    """
    Creates a new 'Size' object having the largest possible size that
    would fit inside target while preserving aspect ratio.
    """
    cls = type(self)
    out = cls()
    if self.aspect > target.aspect:  # Wider than target
      out.__dim_values__ = target.width, int(target.width / self.aspect)
    else:
      out.__dim_values__ = int(target.height * self.aspect), target.height
    return out

  def scaleOuter(self, target: Self) -> Self:
    """
    Creates a new 'Size' object having the smallest possible size that
    would fit outside target while preserving aspect ratio.
    """
    cls = type(self)
    if self.aspect > target.aspect:  # Wider than target
      return cls(target.height * self.aspect, target.height)
    return cls(target.width, target.width / self.aspect)

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
    if key in self.__width_keys__:
      return self.width
    if key in self.__height_keys__:
      return self.height
    return TwoDim._resolveKey(self, key)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
