"""
Point2D is a plain 2D point: integer 'x' and 'y'. A 'BaseObject' with
overloaded constructors accepting plain numbers, a 'QPoint' or 'QPointF'
(strict, so the dispatcher never coerces a Shiboken type), or another point.
Convert out with the 'Q' ('QPoint') and 'QF' ('QPointF') fields.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class Point2D(BaseObject):
  """A 2D point with integer 'x' and 'y'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  x = AttriBox[int](0)
  y = AttriBox[int](0)

  #  Virtual Variables
  Q: Field[QPoint] = Field()
  QF: Field[QPointF] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQPoint(self) -> QPoint:
    return QPoint(self.x, self.y)

  @QF.GET
  def _getQPointF(self) -> QPointF:
    return QPointF(float(self.x), float(self.y))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int)
  def __init__(self, x: int, y: int) -> None:
    self.x, self.y = x, y

  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    self.x, self.y = round(x), round(y)

  @overload(QPoint, strict=True)
  def __init__(self, point: QPoint) -> None:
    self.x, self.y = point.x(), point.y()

  @overload(QPointF, strict=True)
  def __init__(self, point: QPointF) -> None:
    self.x, self.y = round(point.x()), round(point.y())

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.x, self.y = other.x, other.y

  @overload()
  def __init__(self) -> None:
    pass

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self) -> str:
    return 'Point2D(%d, %d)' % (self.x, self.y)

  __repr__ = __str__
