"""
Vector2D subclasses EuclideanObject and encapsulates a plane vector.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointList, QPoint
from PySide6.QtGui import QVector2D
from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload

from . import Point2D
from .. import Eps
from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Type, TypeAlias, Any, Union

  Float: TypeAlias = Union[float, Field]


class Vector2D(EuclideanObject):
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
  mag: Float = Field()
  magSqr: Float = Field()
  unit: Float = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mag.GET
  def _getMag(self, ) -> float:
    return self.magSqr ** 0.5

  @magSqr.GET
  def _getMagSqr(self, ) -> float:
    return self.x ** 2 + self.y ** 2

  @unit.GET
  def _getUnit(self, ) -> Vector2D:
    if self:
      cls = type(self)
      return cls(self.x / self.mag, self.y / self.mag)
    raise ZeroDivisionError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D, Point2D)
  def __init__(self, p: Point2D, q: Point2D) -> None:
    self.x = q.x - p.x
    self.y = q.y - p.y

  @overload(Point2D)
  def __init__(self, p: Point2D) -> None:
    self.__init__(Point2D(0, 0), p)

  @overload(QVector2D)
  def __init__(self, qVector2D: QVector2D) -> None:
    self.x = float(qVector2D.x())
    self.y = float(qVector2D.y())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __mul__(self, other: Self) -> int:
    return self.x * other.x + self.y * other.y

  @overload(QVector2D)
  def __mul__(self, other: QVector2D) -> int:
    return self.x * other.x() + self.y * other.y()

  @overload(THIS)
  def __rshift__(self, other: Self) -> Self:
    """
    The right shift operator returns the projection of the left vector on
    the right.
    """
    if not (self and other):
      raise ZeroDivisionError
    return (self * other) / other.magSqr * other

  @overload(QVector2D)
  def __rshift__(self, other: QVector2D) -> Self:
    return self >> Vector2D(other)

  @overload(THIS)
  def __lshift__(self, other: Self) -> Self:
    """
    The left shift operator reverses the operands. Meaning it returns the
    projection of other on self.
    """
    return other >> self

  @overload(QVector2D)
  def __lshift__(self, other: QVector2D) -> Self:
    return self << Vector2D(other)
