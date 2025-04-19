"""MoveMap maps by translating the values."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.parse import maybe
from worktoy.static import overload
from worktoy.attr import Field

from . import AbstractMap, Point, Region

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class MoveMap(AbstractMap):
  """MoveMap maps by translating the values."""

  #  fallback variables
  __fallback_horizontal__ = 1
  __fallback_vertical__ = 1

  #  private variables
  __horizontal_move__ = None
  __vertical_move__ = None

  #  public variables
  horizontalMove = Field()
  verticalMove = Field()

  #  getter methods
  @horizontalMove.GET
  def _getHorizontalMove(self, ) -> float:
    """Get the horizontal scale."""
    return maybe(self.__horizontal_move__, self.__fallback_horizontal__)

  @verticalMove.GET
  def _getVerticalMove(self, ) -> float:
    """Get the vertical scale."""
    return maybe(self.__vertical_move__, self.__fallback_vertical__)

  #  Caller overloads
  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __call__(self, x: float, y: float) -> tuple[float, float]:
    """Apply the mapping to a point."""
    return float(x) + self.horizontalMove, float(y) + self.verticalMove

  @overload(complex)
  def __call__(self, z: complex) -> complex:
    """Apply the mapping to a complex"""
    out = self(z.real, z.imag)
    return out[0] + out[1] * 1j

  @overload(Point)
  def __call__(self, point: Point) -> Point:
    """Apply the mapping to a point."""
    x = point.x + self.horizontalMove
    y = point.y + self.verticalMove
    return Point(x, y)

  @overload(int)
  @overload(float)
  def __call__(self, value: float) -> tuple[float, float]:
    """Apply the mapping to a single value"""
    return self(value, value)

  @overload(Region)
  def __call__(self, region: Region) -> Region:
    """Apply the mapping to a region."""
    return Region(self(region.topLeft), region.size)

  #  Constructor overloads
  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __init__(self, xMove: float, yMove: float) -> None:
    """Create a ScaleMap."""
    if TYPE_CHECKING:
      assert callable(self)
    self.__horizontal_move__ = xMove
    self.__vertical_move__ = yMove

  @overload(complex)
  def __init__(self, zMove: complex) -> None:
    """Create a ScaleMap."""
    self.__horizontal_move__ = zMove.real
    self.__vertical_move__ = zMove.imag

  @overload(int)
  @overload(float)
  def __init__(self, move: float) -> None:
    """Create a ScaleMap."""
    self.__horizontal_move__ = move
    self.__vertical_move__ = move

  @overload(Point)
  def __init__(self, point: Point) -> None:
    """Create a ScaleMap."""
    self.__horizontal_move__ = point.x
    self.__vertical_move__ = point.y
