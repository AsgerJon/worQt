"""
Size subclasses EuclideanObject and encapsulates a plane size defined by a
width and a height.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF, QSize, QSizeF, QRect, QRectF
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload

from .. import Eps
from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias, Any, Union

  from . import InSets


class Size(EuclideanObject):
  """
Size subclasses EuclideanObject and encapsulates a plane size defined by a
width and a height.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()

  #  Public Variables
  width = Dimension(int, 0, 'w', 'wdt')
  height = Dimension(int, 0, 'h', 'hgt')

  #  Virtual Variables
  area = Field()
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @area.GET
  def _getArea(self, ) -> int:
    return self.width * self.height

  @Q.GET
  def _getQSize(self, ) -> QSize:
    return QSize(self.width, self.height)

  @QF.GET
  def _getQSizeF(self, ) -> QSizeF:
    return QSizeF(float(self.width), float(self.height))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QSize, strict=True)
  def __init__(self, qsize: QSize) -> None:
    self.width = qsize.width()
    self.height = qsize.height()

  @overload(QSizeF, strict=True)
  def __init__(self, sizeF: QSizeF) -> None:
    self.width = int(round(sizeF.width()))
    self.height = int(round(sizeF.height()))

  @overload(QRect, strict=True)
  def __init__(self, rect: QRect) -> None:
    self.width = rect.width()
    self.height = rect.height()

  @overload(QRectF, strict=True)
  def __init__(self, rectF: QRectF) -> None:
    self.width = int(round(rectF.width()))
    self.height = int(round(rectF.height()))

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.width = other.width
    self.height = other.height

  @overload(float, float)
  def __init__(self, width: float, height: float) -> None:
    self.width = int(round(width))
    self.height = int(round(height))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  if TYPE_CHECKING:  # pragma: no cover
    @overload(InSets)
    def __add__(self, other: InSets) -> Self: ...

    @overload(InSets)
    def __sub__(self, other: InSets) -> Self: ...
