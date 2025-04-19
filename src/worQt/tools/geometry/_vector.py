"""Vector class for 2D and 3D coordinates."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import Point

try:
  from typing import TYPE_CHECKING, Any
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self


class Vector(Point):
  """Vector subclasses Point and provides a vector in 2D space."""

  def __mul__(self, other: Self) -> Any:
    """The * multiplication with float or int applies component wise,
    otherwise it applies the dot product."""
    if isinstance(other, (int, float)):
      return Vector(self.x * other, self.y * other)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self.x * other.x + self.y * other.y

  def __matmul__(self, other: Self) -> Any:
    """The @ operator applies the cross product."""
    if isinstance(other, (int, float)):
      return Vector(self.x * other, self.y * other)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self.x * other.y - self.y * other.x

  def __invert__(self) -> Self:
    """Returns the hat-vector. """
    return Vector(-self.y, self.x)

  def __rshift__(self, other: Any) -> Self:
    """The >> projects self onto other vector."""
    if isinstance(other, (int, float)):
      return NotImplemented
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not other:
      raise ZeroDivisionError
    return self * other / (other * other) * other

  def __lshift__(self, other: Any) -> Self:
    """The << projects other vector onto self."""
    if isinstance(other, (int, float)):
      return NotImplemented
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if not other:
      raise ZeroDivisionError
    return other * self / (self * self) * self

  def __rrshift__(self, other: Any) -> Self:
    """The >> operator projects self onto other vector."""
    return self << other

  def __rlshift__(self, other: Any) -> Self:
    """The << operator projects other vector onto self."""
    return self >> other
