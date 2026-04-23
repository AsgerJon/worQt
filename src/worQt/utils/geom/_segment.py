"""
Segment subclasses EuclideanObject and encapsulates a line segment
spanning two points. Instances are defined by 'x' and 'y' specifying one
of the points and 'width' and 'height' specifying the vector from that
point to the other point.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointList, QPoint, QPointF
from PySide6.QtGui import QVector2D
from worktoy.desc import Field
from worktoy.dispatch import overload

from . import Point2D, Vector2D, Line
from .euclid import EuclideanObject, Dimension

if TYPE_CHECKING:  # pragma: no cover
  from . import Rect


class Segment(EuclideanObject):
  """
  Segment subclasses EuclideanObject and encapsulates a line segment
  spanning two points. Instances are defined by 'x' and 'y' specifying one
  of the points and 'width' and 'height' specifying the vector from that
  point to the other point.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  xP = Dimension(int, 0, 'x0', 'x_start', 'x1')
  yP = Dimension(int, 0, 'y0', 'y_start', 'y1')
  xQ = Dimension(int, 0, 'x1', 'x_end', 'x2', 'width')
  yQ = Dimension(int, 0, 'y1', 'y_end', 'y2', 'height')

  #  Virtual Variables
  P = Field()  # Point2D object
  Q = Field()  # Point2D object
  r = Field()  # Vector2D object
  length = Field()  # float
  line = Field()  # Line object
  boundingRect = Field()  # Rect object

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @P.GET
  def _getP(self, ) -> Point2D:
    return Point2D(self.xP, self.yP)

  @Q.GET
  def _getQ(self, ) -> Point2D:
    return Point2D(self.xQ, self.yQ)

  @r.GET
  def _getR(self, ) -> Vector2D:
    return Vector2D(self.rX, self.rY)

  @length.GET
  def _getLength(self, ) -> float:
    raise NotImplementedError

  @line.GET
  def _getLine(self, ) -> Line:
    raise NotImplementedError

  @boundingRect.GET
  def _getBoundingRect(self, ) -> Rect:
    from . import Rect
    left = min(self.xP, self.xQ)
    top = min(self.yP, self.yQ)
    right = max(self.xP, self.xQ)
    bottom = max(self.yP, self.yQ)
    return Rect(left=left, top=top, right=right, bottom=bottom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D)
  def __contains__(self, point: Point2D) -> bool:
    if point not in self.boundingRect:
      return False
    return True if point in self.line else False

  @overload(QPoint)
  @overload(QPointF)
  def __contains__(self, point: QPoint) -> bool:
    return True if Point2D(point) in self else False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Point2D, Point2D)
  def __init__(self, pointP: Point2D, pointQ: Point2D) -> None:
    self.xP = pointP.x
    self.yP = pointP.y
    self.xQ = pointQ.x
    self.yQ = pointQ.y

  @overload(QPoint, QPoint)
  @overload(QPointF, QPointF)
  @overload(QPoint, QPointF)
  @overload(QPointF, QPoint)
  def __init__(self, pointP: QPoint, pointQ: QPoint) -> None:
    self.__init__(Point2D(pointP), Point2D(pointQ))

  @overload(Point2D, Vector2D)
  def __init__(self, pointP: Point2D, vectorPQ: Vector2D) -> None:
    self.xP = pointP.x
    self.yP = pointP.y
    self.xQ = pointP.x + vectorPQ.x
    self.yQ = pointP.y + vectorPQ.y

  @overload(QPoint, QVector2D)
  @overload(QPointF, QVector2D)
  def __init__(self, pointP: QPoint, vectorPQ: QVector2D) -> None:
    self.__init__(Point2D(pointP), Vector2D(vectorPQ))

  @overload(QVector2D, QPoint)
  @overload(QVector2D, QPointF)
  @overload(Vector2D, Point2D)
  def __init__(self, vectorPQ: Vector2D, pointQ: Point2D) -> None:
    self.__init__(pointQ, vectorPQ)
