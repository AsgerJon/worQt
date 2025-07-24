"""Vector2D encapsulates plane vectors."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.utilities.mathematics import atan2

from . import Point2D

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any, Iterator


class Vector2D(Point2D):
  """Vector2D encapsulates plane vectors."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables

  #  Virtual Variables
  ABS = Field()
  ANG = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @ABS.GET
  def _getAbs(self, **kwargs) -> float:
    """Get the absolute value of the vector."""
    return (self.x ** 2 + self.y ** 2) ** 0.5

  @ANG.GET
  def _getAng(self, **kwargs) -> float:
    """Get the angle of the vector in radians."""
    if self:
      return atan2(self.y, self.x)
    raise ZeroDivisionError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS, THIS)
  def __init__(self, P0: Self, P1: Self) -> None:
    self.__private_x__ = P1.x - P0.x
    self.__private_y__ = P1.y - P0.y

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __abs__(self, ) -> float:
    """Get the absolute value of the vector."""
    return self.ABS

  def __neg__(self) -> Self:
    """Get the negated vector."""
    return Vector2D(-self.x, -self.y)

  @overload(float)
  def __mul__(self, other: float) -> Self:
    """Multiply the vector by a scalar."""
    return Vector2D(self.x * other, self.y * other)

  @overload(THIS)
  def __mul__(self, other: Self) -> float:
    """Dot product of two vectors."""
    return self.x * other.x + self.y * other.y

  @overload.fallback
  def __mul__(self, other: Any) -> NotImplemented:
    """Fallback for unsupported multiplication."""
    return NotImplemented

  @overload(float)
  def __matmul__(self, other: float) -> Self:
    """Multiply the vector by a scalar using @ operator."""
    return Vector2D(self.x * other, self.y * other)

  @overload(THIS)
  def __matmul__(self, other: Self) -> float:
    """2D pseudo-cross product of two vectors."""
    return self.x * other.y - self.y * other.x

  @overload.fallback
  def __matmul__(self, other: Any) -> NotImplemented:
    """Fallback for unsupported matrix multiplication."""
    return NotImplemented

  def __truediv__(self, other: float) -> Self:
    """Divide the vector by a scalar."""
    if other:
      return self * (1 / other)
    raise ZeroDivisionError

  def __rshift__(self, other: Self) -> Self:
    """Returns the projection of self onto another vector."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    if self and other:
      return other * (self @ other) / (other @ other)
    raise ZeroDivisionError

  def __lshift__(self, other: Self) -> Self:
    """Returns the projection of another vector onto self."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return other >> self

  def __add__(self, other: Self) -> Self:
    """Add two vectors."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return type(self)(self.x + other.x, self.y + other.y)

  def __sub__(self, other: Self) -> Self:
    """Subtract two vectors."""
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    return self + (-other)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
