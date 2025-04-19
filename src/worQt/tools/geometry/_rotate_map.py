"""RotateMap rotates points about the origin. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import atan2, cos, sin

from worktoy.attr import Field
from worktoy.mcls import AbstractMetaclass
from worktoy.parse import maybe
from worktoy.static import overload
from worktoy.text import typeMsg
from worktoy.waitaminute import MissingVariable, VariableNotNone

from . import AbstractMap, Point, Region, Size, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Callable, Self, TypeAlias, Optional

  Floats: TypeAlias = Optional[tuple[float, float]]


class RotateMap(AbstractMap):
  """RotateMap rotates points about the origin. """

  #  fallback variables
  __fallback_angle__ = 0

  #  private variables
  __rotation_angle__ = None

  #  public variables
  angle = Field()

  #  getter methods
  @angle.GET
  def _getAngle(self, ) -> float:
    """Get the angle of rotation."""
    return maybe(self.__rotation_angle__, self.__fallback_angle__)

  #  caller overloads
  @overload(Point)
  def __call__(self, point: Point) -> Point:
    """Rotate point about the origin."""
    if not point.x ** 2 + point.y ** 2:
      raise ZeroDivisionError
    r = (point.x ** 2 + point.y ** 2) ** 0.5
    t0 = atan2(point.y, point.x)
    t = t0 + self.angle
    x = r * cos(t)
    y = r * sin(t)
    return Point(x, y)

  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __call__(self, x: float, y: float) -> Floats:
    """Rotate point about the origin."""
    if TYPE_CHECKING:
      assert callable(self)
    if not x ** 2 + y ** 2:
      try:
        print("""Before ZeroDivisionError""")
        print("""Received: x = %s, y = %s""" % (str(x), str(y)))
        raise ZeroDivisionError
      finally:
        print("""After ZeroDivisionError""")
    p = self(Point(x, y))
    return p.x, p.y

  @overload(Vector)
  def __call__(self, vector: Vector) -> Vector:
    """Rotate vector about the origin."""
    if TYPE_CHECKING:
      assert callable(self)
    p0 = Point(vector.x, vector.y)
    p = self(p0)
    return Vector(p.x, p.y)

  @overload(complex)
  def __call__(self, z: complex) -> complex:
    """Rotate complex number about the origin."""
    if TYPE_CHECKING:
      assert callable(self)
    if not z.real ** 2 + z.imag ** 2:
      raise ZeroDivisionError
    x, y = self(z.real, z.imag)
    return x + y * 1j

  @overload(float)
  @overload(int)
  def __call__(self, value: float) -> tuple[float, float]:
    """Rotate float about the origin."""
    if TYPE_CHECKING:
      assert callable(self)
    return self(value, value)

  #  constructor overloads
  @overload(float)
  @overload(int)
  def __init__(self, angle: float) -> None:
    """RotateMap constructor."""
    self.__rotation_angle__ = float(angle)

  @overload(complex)
  def __init__(self, z: complex) -> None:
    """RotateMap constructor."""
    self.__rotation_angle__ = float(abs(z))

  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    """RotateMap constructor."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(abs(float(x) + float(y) * 1j))
