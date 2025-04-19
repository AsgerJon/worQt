"""ScaleMap provides a mapping between two objects that linearly scales."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.parse import maybe
from worktoy.static import overload, THIS
from worktoy.attr import Field

from . import AbstractMap, Point, Region, Size, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Callable, Self


class ScaleMap(AbstractMap):
  """ScaleMap provides a mapping between two objects that linearly scales."""

  #  fallback variables
  __fallback_horizontal__ = 1
  __fallback_vertical__ = 1

  #  private variables
  __horizontal_scale__ = None
  __vertical_scale__ = None

  #  public variables
  horizontalScale = Field()
  verticalScale = Field()

  #  getter methods
  @horizontalScale.GET
  def _getHorizontalScale(self, ) -> float:
    """Get the horizontal scale."""
    return maybe(self.__horizontal_scale__, self.__fallback_horizontal__)

  @verticalScale.GET
  def _getVerticalScale(self, ) -> float:
    """Get the vertical scale."""
    return maybe(self.__vertical_scale__, self.__fallback_vertical__)

  #  Caller overloads
  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __call__(self, x: float, y: float, **kwargs) -> tuple[float, float]:
    """Apply the mapping to a point."""
    return x * self.horizontalScale, y * self.verticalScale

  @overload(Point)
  def __call__(self, point: Point, **kwargs) -> Point:
    """Apply the mapping to a point."""
    x = point.x * self.horizontalScale
    y = point.y * self.verticalScale
    return Point(x, y, **kwargs)

  @overload(Size)
  def __call__(self, size: Size, **kwargs) -> Size:
    """Apply the mapping to a size."""
    width = size.width * self.horizontalScale
    height = size.height * self.verticalScale
    return Size(width, height, **kwargs)

  @overload(Region)
  def __call__(self, region: Region, **kwargs) -> Region:
    """Apply the mapping to a region."""
    topLeft = region.topLeft
    bottomRight = region.bottomRight
    x0 = topLeft.x
    y0 = topLeft.y
    x1 = bottomRight.x
    y1 = bottomRight.y
    dx, dy = x1 - x0, y1 - y0
    x2 = x0 + dx * self.horizontalScale
    y2 = y0 + dy * self.verticalScale
    return Region(x0, y0, x2, y2, **kwargs)

  #  Constructor overloads
  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __init__(self, xScale: float, yScale: float, **kwargs) -> None:
    """Create a ScaleMap."""
    if TYPE_CHECKING:
      assert callable(self)
    if xScale < 0 or yScale < 0:
      raise ValueError('Scale factors must be non-negative.')
    self.__horizontal_scale__ = xScale
    self.__vertical_scale__ = yScale

  @overload(complex)
  def __init__(self, zScale: complex, **kwargs) -> None:
    """Create a ScaleMap."""
    xScale, yScale = zScale.real, zScale.imag
    if xScale < 0 or yScale < 0:
      raise ValueError('Scale factors must be non-negative.')
    self.__horizontal_scale__ = xScale
    self.__vertical_scale__ = yScale

  @overload(int)
  @overload(float)
  def __init__(self, scale: float, **kwargs) -> None:
    """Create a ScaleMap."""
    if scale < 0:
      raise ValueError('Scale factors must be non-negative.')
    self.__horizontal_scale__ = scale
    self.__vertical_scale__ = scale

  @overload(Point)
  def __init__(self, point: Point, **kwargs) -> None:
    """Create a ScaleMap."""
    xScale, yScale = point.x, point.y
    if xScale < 0 or yScale < 0:
      raise ValueError('Scale factors must be non-negative.')
    self.__horizontal_scale__ = xScale
    self.__vertical_scale__ = yScale

  @overload(Vector)
  def __init__(self, vector: Vector, **kwargs) -> None:
    """Create a ScaleMap."""
    xScale, yScale = vector.x, vector.y
    if xScale < 0 or yScale < 0:
      raise ValueError('Scale factors must be non-negative.')
    self.__horizontal_scale__ = xScale
    self.__vertical_scale__ = yScale
