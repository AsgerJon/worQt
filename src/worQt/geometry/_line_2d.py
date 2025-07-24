"""Line2D implements plane lines. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from . import Point2D, Vector2D

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator


class Line2D(BaseObject):
  """Line2D implements plane lines. """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __origin_x__ = 0.0
  __origin_y__ = 0.0
  __direction_x__ = 1.0
  __direction_y__ = 0.0

  #  Private Variables
  __origin_point__ = None
  __direction_vector__ = None

  #  Public Variables
  origin = Field()
  direction = Field()

  #  Virtual Variables
  originVector = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @origin.GET
  def _getOrigin(self, **kwargs) -> Point2D:
    """Get the origin point of the line."""
    if self.__origin_point__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__origin_point__ = Point2D(self.__origin_x__, self.__origin_y__)
      return self._getOrigin(_recursion=True)
    return self.__origin_point__

  @direction.GET
  def _getDirection(self, **kwargs) -> Vector2D:
    """Get the direction vector of the line."""
    if self.__direction_vector__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      x, y = self.__direction_x__, self.__direction_y__
      self.__direction_vector__ = Vector2D(x, y)
      return self._getDirection(_recursion=True)
    return self.__direction_vector__

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
  def __sub__(self, P: Point2D) -> float:
    P0 = self.origin
    r = self.direction
    P0P = Vector2D(P) - Vector2D(P0)
    return abs(P0P - ((P0P * r) / abs(r) ** 2) * r)

  @overload.fallback
  def __sub__(self, ) -> NotImplemented:
    """Subtraction is not implemented for this type."""
    return NotImplemented

  @overload(Vector2D)
  def __rrshift__(self, other: Vector2D) -> Vector2D:
    return other >> self.direction

  @overload(Point2D)
  def __rrshift__(self, other: Point2D) -> Point2D:
    """Get the distance from a point to the line."""
    P0, P = self.origin, other
    r = self.direction
    P0P = Vector2D(P) - Vector2D(P0)
    return P0 + ((P0P * r) / abs(r) ** 2) * r

  @overload.fallback
  def __rrshift__(self, other: Any) -> NotImplemented:
    """Right shift is not implemented for this type."""
    return NotImplemented

  @overload(Vector2D)
  def __lshift__(self, other: Vector2D) -> Vector2D:
    """Get the distance from a vector to the line."""
    return other >> self

  @overload(Point2D)
  def __lshift__(self, other: Point2D) -> Point2D:
    """Get the distance from a point to the line."""
    return other >> self

  @overload.fallback
  def __lshift__(self, other: Any) -> NotImplemented:
    """Left shift is not implemented for this type."""
    return NotImplemented

  @overload(THIS)
  def __and__(self, other: Self) -> Point2D:
    """Get the intersection point of two lines."""
    P0, P1 = self.origin, other.origin
    r0, r1 = self.direction, other.direction
    denominator = r0.x * r1.y - r0.y * r1.x
    if denominator:
      t = ((P1.x - P0.x) * r1.y - (P1.y - P0.y) * r1.x) / denominator
      return P0 + t * r0
    raise ZeroDivisionError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
