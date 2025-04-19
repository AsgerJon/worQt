"""RegionMap subclasses AbstractMap and provides a mapping between two
regions applied to points. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field
from worktoy.static import overload, THIS

from . import AbstractMap, Point, Region, Size

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Callable, Self


class RegionMap(AbstractMap):
  """RegionMap subclasses AbstractMap and provides a mapping between two
  regions applied to points. """

  #  fallback variables
  __fallback_source_region__ = (0, 0, 1, 1,)
  __fallback_target_region__ = (0, 0, 1, 1,)

  #  private variables
  __source_region__ = None
  __target_region__ = None

  #  public variables
  source = Field()
  target = Field()

  #  getter methods
  @source.GET
  def _getSource(self, ) -> Region:
    """Get the source region."""
    if self.__source_region__ is None:
      return Region(*self.__fallback_source_region__)
    return self.__source_region__

  @target.GET
  def _getTarget(self, ) -> Region:
    """Get the target region."""
    if self.__target_region__ is None:
      return Region(*self.__fallback_target_region__)
    return self.__target_region__

  #  caller overloads
  @overload(Region)
  def __call__(self, region: Region, **kwargs) -> Region:
    """Apply the mapping to a region."""
    if TYPE_CHECKING:
      assert callable(self)
    return Region(self(region.topLeft), self(region.bottomRight), **kwargs)

  @overload(Point)
  def __call__(self, point: Point, **kwargs) -> Point:
    """Apply the mapping to a point."""
    x = point.x - self.source.left
    y = point.y - self.source.top
    dx, dy = x / self.source.width, y / self.source.height
    outX = self.target.left + dx * self.target.width
    outY = self.target.top + dy * self.target.height
    return Point(outX, outY, **kwargs)

  @overload(int, int)
  @overload(float, int)
  @overload(int, float)
  @overload(float, float)
  def __call__(self, x: float, y: float, **kwargs) -> tuple[float, float]:
    """Apply the mapping to a point."""
    if TYPE_CHECKING:
      assert callable(self)
    point = self(Point(x, y), **kwargs)
    return point.x, point.y

  @overload(complex)
  def __call__(self, z: complex, **kwargs) -> complex:
    """Apply the mapping to a point."""
    if TYPE_CHECKING:
      assert callable(self)
    point = self(Point(z), **kwargs)
    return point.x + point.y * 1j

  @overload(tuple)
  @overload(list)
  def __call__(self, vals: Any, **kwargs) -> tuple[float, float]:
    """Apply the mapping to a point."""
    if TYPE_CHECKING:
      assert callable(self)
    return self(*vals, **kwargs)

  #  constructor overloads

  @overload(Region, Region)
  def __init__(self, source: Region, target: Region) -> None:
    """Apply the mapping to a region."""
    self.__source_region__ = source
    self.__target_region__ = target

  @overload(Region, Size)
  def __init__(self, source: Region, target: Size) -> None:
    """Apply the mapping to a region."""
    self.__source_region__ = source
    self.__target_region__ = Region(target)

  @overload(Size, Region)
  def __init__(self, source: Size, target: Region) -> None:
    """Apply the mapping to a region."""
    self.__source_region__ = Region(source)
    self.__target_region__ = target

  @overload(Region)
  def __init__(self, target: Region) -> None:
    """Apply the mapping to a region."""
    self.__target_region__ = target

  @overload(Size)
  def __init__(self, target: Size) -> None:
    """Apply the mapping to a region."""
    self.__target_region__ = Region(target)

  @overload()
  def __init__(self) -> None:
    """Apply the mapping to a region."""
    pass
