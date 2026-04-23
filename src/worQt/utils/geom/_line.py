"""
Line encapsulates continuous lines. Unlike 'Segment', 'Line' objects have
no extend or rather extend infinitely in both directions. Internally,
they are defined by a point and a vector. They can be instantiated by
providing a point and a vector, two distinct points or a float to float
function.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF
from PySide6.QtGui import QVector2D
from worktoy.dispatch import overload
from worktoy.utilities import textFmt
from worktoy.desc import Field

from . import Point2D, Vector2D
from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, Union, TypeAlias, Any

  Func: TypeAlias = Callable[[float], float]

  Float: TypeAlias = Union[float, Field]
  Point: TypeAlias = Union[Point2D, Field]
  Vector: TypeAlias = Union[Vector2D, Field]


class Line(EuclideanObject):
  """
  Line encapsulates continuous lines. Unlike 'Segment', 'Line' objects have
  no extend or rather extend infinitely in both directions. Internally,
  they are defined by a point and a vector. They can be instantiated by
  providing a point and a vector, two distinct points or a float to float
  function.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  #  #  Initial Point
  x0 = Dimension(int, 0, 'x0', 'x_start', 'x1')
  y0 = Dimension(int, 0, 'y0', 'y_start', 'y1')
  #  #  Direction Vector
  rX = Dimension(int, 1, 'rX', 'x_extend', 'x2')
  rY = Dimension(int, 1, 'rY', 'y_extend', 'y2')

  #  Virtual Variables
  P0: Point = Field()
  r: Vector = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @P0.GET
  def _getP0(self, ) -> Point2D:
    return Point2D(self.x0, self.y0)

  @r.GET
  def _getR(self, ) -> Point2D:
    vector = Vector2D(self.rX, self.rY)
    if vector.mag > self.eps:
      return vector
    raise ZeroDivisionError

  def equation(self, x: float) -> float:
    """
    Returns the 'y' coordinate for the point on the line with the given
    'x' value.
    """
    slope = self.rY / self.rX
    intercept = self.y0 - slope * self.x0
    return slope * x + intercept

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D)
  def __contains__(self, point: Point2D) -> bool:
    eq = self.equation
    if abs(point.y - eq(point.x)) > self.eps:
      return False
    return True

  @overload(Vector2D)
  def __rrshift__(self, other: Vector2D) -> Vector2D:
    """
    Returns the projection of the given vector onto the line.
    """
    return other >> self.r

  @overload(QVector2D)
  def __rrshift__(self, other: QVector2D) -> Vector2D:
    """
    Returns the projection of the given vector onto the line.
    """
    return Vector2D(other) >> self.r

  @overload(Vector2D)
  def __rlshift__(self, other: Vector2D) -> Vector2D:
    """
    Reverses the order of the operands.
    """
    return self >> other

  @overload(QVector2D)
  def __rlshift__(self, other: QVector2D) -> Vector2D:
    """
    Reverses the order of the operands.
    """
    return self >> Vector2D(other)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D, Vector2D)
  def __init__(self, point: Point2D, vector: Vector2D) -> None:
    self.x0 = point.x
    self.y0 = point.y
    self.rX = vector.x
    self.rY = vector.y
    super().__init__()

  @overload(QVector2D, QPoint)
  @overload(QVector2D, QPointF)
  @overload(Vector2D, Point2D)
  def __init__(self, vector: Vector2D, point: Point2D) -> None:
    self.__init__(point, vector)

  @overload(Point2D, Point2D)
  def __init__(self, point1: Point2D, point2: Point2D) -> None:
    r = Vector2D(point1, point2)
    self.__init__(point1, r)

  @overload(QPoint, QPoint)
  @overload(QPointF, QPointF)
  @overload(QPoint, QPointF)
  @overload(QPointF, QPoint)
  def __init__(self, point1: QPoint, point2: QPoint) -> None:
    self.__init__(Point2D(point1), Point2D(point2))

  @overload(QPoint, QVector2D)
  @overload(QPointF, QVector2D)
  def __init__(self, point: QPoint, vector: QVector2D) -> None:
    self.__init__(Point2D(point), Vector2D(vector))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D)
  def dist(self, point: Point2D) -> float:
    """
    Returns the distance from the line to the given point.
    """
    P0P = Vector2D(self.P0, point)
    return abs(P0P - P0P >> self.r)

  @overload(QPoint, strict=True)
  @overload(QPointF, strict=True)
  def dist(self, point: QPoint) -> float:
    return self.dist(Point2D(point))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
