"""RotatePointMap rotates points by a given angle about a given point. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import atan2, cos, sin

from worktoy.attr import Field
from worktoy.parse import maybe
from worktoy.static import overload, THIS
from worktoy.waitaminute import VariableNotNone

from . import AbstractMap, Point, Region, Size, MoveMap, RotateMap, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Callable, Self


class RotatePointMap(AbstractMap):
  """RotatePointMap rotates points by a given angle about a given point."""

  #  fallback variables
  __fallback_angle__ = 0
  __fallback_center__ = (0, 0)

  #  private variables
  __rotation_angle__ = None
  __rotation_center__ = None
  __move_map__ = None
  __rotate_map__ = None
  __return_map__ = None

  #  public variables
  angle = Field()
  center = Field()
  moveMap = Field()
  rotateMap = Field()
  returnMap = Field()

  #  creator methods
  def _createMoveMap(self, ) -> None:
    """Create a MoveMap."""
    if self.__move_map__ is not None:
      raise VariableNotNone('__move_map__', )
    self.__move_map__ = MoveMap(self.center)

  def _createRotateMap(self, ) -> None:
    """Create a RotateMap."""
    if self.__rotate_map__ is not None:
      raise VariableNotNone('__rotate_map__', )
    self.__rotate_map__ = RotateMap(self.angle)

  def _createReturnMap(self, ) -> None:
    """Create a ReturnMap."""
    if self.__return_map__ is not None:
      raise VariableNotNone('__return_map__', )
    self.__return_map__ = MoveMap(-self.center.x, -self.center.y)

  #  getter methods
  @angle.GET
  def _getAngle(self, ) -> float:
    """Get the angle of rotation."""
    return maybe(self.__rotation_angle__, self.__fallback_angle__)

  @center.GET
  def _getCenter(self, ) -> Point:
    """Get the center of rotation."""
    if self.__rotation_center__ is None:
      return Point(*self.__fallback_center__)
    return self.__rotation_center__

  @moveMap.GET
  def _getMoveMap(self, **kwargs) -> MoveMap:
    """Get the move map."""
    if self.__move_map__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createMoveMap()
      return self._getMoveMap(_recursion=True)
    return self.__move_map__

  @rotateMap.GET
  def _getRotateMap(self, **kwargs) -> RotateMap:
    """Get the rotate map."""
    if self.__rotate_map__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createRotateMap()
      return self._getRotateMap(_recursion=True)
    return self.__rotate_map__

  @returnMap.GET
  def _getReturnMap(self, **kwargs) -> MoveMap:
    """Get the return map."""
    if self.__return_map__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createReturnMap()
      return self._getReturnMap(_recursion=True)
    return self.__return_map__

  #  caller overloads
  @overload(Point)
  def __call__(self, point: Point) -> Point:
    """Rotate point about the center."""
    if not point.x ** 2 + point.y ** 2:
      raise ZeroDivisionError
    move = self.moveMap(point)
    rotate = self.rotateMap(move)
    return self.returnMap(rotate)

  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __call__(self, x: float, y: float) -> tuple[float, float]:
    """Rotate point about the center."""
    if TYPE_CHECKING:
      assert callable(self)
    if not x ** 2 + y ** 2:
      raise ZeroDivisionError
    p = self(Point(x, y))
    return p.x, p.y

  @overload(complex)
  def __call__(self, z: complex) -> complex:
    """Rotate point about the center."""
    if TYPE_CHECKING:
      assert callable(self)
    z1 = self(z.real, z.imag)
    return z1.x + z1.y * 1j

  #  constructor overloads
  @overload(Point, float)
  def __init__(self, point: Point, angle: float) -> None:
    """RotatePointMap constructor."""
    self.__rotation_center__ = point
    self.__rotation_angle__ = angle

  @overload(float, float, float)
  def __init__(self, x: float, y: float, angle: float) -> None:
    """RotatePointMap constructor."""
    self.__rotation_center__ = Point(x, y)
    self.__rotation_angle__ = angle

  @overload(Point, Vector)
  def __init__(self, point: Point, vector: Vector) -> None:
    """RotatePointMap constructor."""
    P0P = Vector(self.center, point)
    r = vector >> ~P0P
    self.__rotation_center__ = point
    self.__rotation_angle__ = atan2(r.y, r.x)
