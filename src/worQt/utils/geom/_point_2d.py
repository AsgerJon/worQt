"""
Point2D subclasses EuclideanObject and encapsulates a plane position.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QMouseEvent, QEventPoint
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.waitaminute import TypeException
from worktoy.waitaminute.dispatch import DispatchException

from .. import Eps
from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias


class Point2D(EuclideanObject):
  """
  Vector2D provides the base class for two dimensional geometric classes.
  These are immutable.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  eps = Eps()

  #  Public Variables
  x = Dimension(int, 0, 'horizontal', 'col', 'column')
  y = Dimension(int, 0, 'vertical', 'row')

  #  Virtual Variables
  Q = Field()
  QF = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQPoint(self, ) -> QPoint:
    return QPoint(self.x, self.y)

  @QF.GET
  def _getQPointF(self, ) -> QPointF:
    return QPoint.toPointF(self.Q)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QPoint, strict=True)
  def __init__(self, qPoint: QPoint, ) -> None:
    self.__init__(qPoint.x(), qPoint.y())

  @overload(QPointF, strict=True)
  def __init__(self, qPointF: QPointF, ) -> None:
    self.__init__(qPointF.x(), qPointF.y())

  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    self.__init__(int(round(x)), int(round(y)), )

  @overload(QMouseEvent, strict=True)
  def __init__(self, qMouseEvent: QMouseEvent, ) -> None:
    eventPoint, *_ = (*QMouseEvent.points(qMouseEvent), None)
    if isinstance(eventPoint, QEventPoint):
      self.__init__(eventPoint)
    else:
      raise TypeException('eventPoint', eventPoint, QEventPoint)

  @overload(QEventPoint, strict=True)
  def __init__(self, eventPoint: QEventPoint, ) -> None:
    self.__init__(QEventPoint.position(eventPoint))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def dist(self, other: Self) -> float:
    return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

  @overload(QPointF, strict=True)
  @overload(QPoint, strict=True)
  def dist(self, other: QPoint) -> float:
    return ((other.x() - self.x) ** 2 + (other.y() - self.y) ** 2) ** 0.5

  @overload.fallback
  def dist(self, other: object) -> float:
    try:
      func = getattr(other, 'dist')
    except AttributeError as attributeError:
      cls = type(self)
      raise DispatchException(cls.dist, (other,)) from attributeError
    else:
      return func(self)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
