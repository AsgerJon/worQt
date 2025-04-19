"""Region represents a region spanning between two points in 2D space."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field
from worktoy.mcls import BaseObject
from worktoy.parse import maybe
from worktoy.static import overload, THIS
from worktoy.waitaminute import DispatchException

from . import Point, Size

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Any, Self, Never


class Region(BaseObject):
  """Region represents a region spanning between two points in 2D space."""

  #  fallback value
  __fallback_left__ = 0
  __fallback_top__ = 0
  __fallback_right__ = 0
  __fallback_bottom__ = 0

  #  private variables
  __left_edge__ = None
  __top_edge__ = None
  __right_edge__ = None
  __bottom_edge__ = None

  #  public variables
  left = Field()
  top = Field()
  right = Field()
  bottom = Field()

  #  virtual variables
  # - - edges
  hCenter = Field()
  horizontalCenter = Field()
  vCenter = Field()
  verticalCenter = Field()
  # - - points
  topLeft = Field()
  topRight = Field()
  bottomRight = Field()
  bottomLeft = Field()
  center = Field()
  # - - dimensions
  width = Field()
  height = Field()
  area = Field()
  size = Field()
  aspect = Field()

  #  public getters
  @left.GET
  def _getLeft(self) -> float:
    """Get the left edge of the region."""
    left = maybe(self.__left_edge__, self.__fallback_left__)
    right = maybe(self.__right_edge__, self.__fallback_right__)
    return min(left, right)

  @top.GET
  def _getTop(self) -> float:
    """Get the top edge of the region."""
    top = maybe(self.__top_edge__, self.__fallback_top__)
    bottom = maybe(self.__bottom_edge__, self.__fallback_bottom__)
    return min(top, bottom)

  @right.GET
  def _getRight(self) -> float:
    """Get the right edge of the region."""
    left = maybe(self.__left_edge__, self.__fallback_left__)
    right = maybe(self.__right_edge__, self.__fallback_right__)
    return max(left, right)

  @bottom.GET
  def _getBottom(self) -> float:
    """Get the bottom edge of the region."""
    top = maybe(self.__top_edge__, self.__fallback_top__)
    bottom = maybe(self.__bottom_edge__, self.__fallback_bottom__)
    return max(top, bottom)

  #  virtual getters
  # - Edges
  @hCenter.GET
  @horizontalCenter.GET
  def _getHorizontalCenter(self) -> float:
    """Get the horizontal center of the region."""
    return (self.left + self.right) / 2

  @vCenter.GET
  @verticalCenter.GET
  def _getVerticalCenter(self) -> float:
    """Get the vertical center of the region."""
    return (self.top + self.bottom) / 2

  # - Points
  @topLeft.GET
  def _getTopLeft(self) -> Point:
    """Get the top left point of the region."""
    return Point(self.left, self.top)

  @topRight.GET
  def _getTopRight(self) -> Point:
    """Get the top right point of the region."""
    return Point(self.right, self.top)

  @bottomRight.GET
  def _getBottomRight(self) -> Point:
    """Get the bottom right point of the region."""
    return Point(self.right, self.bottom)

  @bottomLeft.GET
  def _getBottomLeft(self) -> Point:
    """Get the bottom left point of the region."""
    return Point(self.left, self.bottom)

  @center.GET
  def _getCenter(self) -> Point:
    """Get the center point of the region."""
    return Point(self.horizontalCenter, self.verticalCenter)

  # - Dimensions
  @width.GET
  def _getWidth(self) -> float:
    """Get the width of the region."""
    return self.right - self.left

  @height.GET
  def _getHeight(self) -> float:
    """Get the height of the region."""
    return self.bottom - self.top

  @area.GET
  def _getArea(self) -> float:
    """Get the area of the region."""
    return self.width * self.height

  @aspect.GET
  def _getAspect(self) -> float:
    """Get the aspect ratio of the region."""
    if not self.height:
      raise ZeroDivisionError
    if not self.width:
      return 0
    return self.width / self.height

  @size.GET
  def _getSize(self) -> Size:
    """Get the size of the region."""
    return Size(self.width, self.height)

  def __bool__(self) -> bool:
    """Check if the region is empty."""
    return True if self.width and self.height else False

  #  Constructors

  @overload(int, int, int, int)
  @overload(float, float, float, float)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given edges."""
    self.__left_edge__ = float(args[0])
    self.__top_edge__ = float(args[1])
    self.__right_edge__ = float(args[2])
    self.__bottom_edge__ = float(args[3])

  @overload(Point, Point)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given points."""
    try:
      p1, p2 = args
    except Exception as exception:
      raise DispatchException from exception
    else:
      self.__left_edge__ = float(min(p1.x, p2.x))
      self.__top_edge__ = float(min(p1.y, p2.y))
      self.__right_edge__ = float(max(p1.x, p2.x))
      self.__bottom_edge__ = float(max(p1.y, p2.y))
    finally:
      pass

  @overload(complex, complex)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given edges."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    z1, z2 = args
    self.__init__(Point(z1), Point(z2), **kwargs)

  @overload(Point, Size)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given point and size."""
    if kwargs.get('_verbose', False):
      print("""__init__(Point, Size)""")
      print("""args: %s""" % (str(args),))
      print("""kwargs: %s""" % (str(kwargs),))
    p, s = args
    self.__left_edge__ = float(p.x)
    self.__top_edge__ = float(p.y)
    self.__right_edge__ = float(p.x + s.width)
    self.__bottom_edge__ = float(p.y + s.height)

  @overload(Size, Point)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given size and point."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    s, p = args
    self.__init__(p, s, **kwargs)

  @overload(Point)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given point."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    point = args[0]
    posArgs = point.x, point.y, point.x, point.y
    self.__init__(*posArgs, **kwargs)

  @overload(Size)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given size."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    size = args[0]
    self.__init__(Point(0, 0), size, **kwargs)

  @overload(complex)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given complex number."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    z = args[0]
    self.__init__(Point(z), Point(z), **kwargs)

  @overload(int, int)
  @overload(float, float)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given edges."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(*args, *args, **kwargs)

  @overload(THIS)
  def __init__(self, *args, **kwargs) -> None:
    """Initialize the region with the given region."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    other = args[0]
    posArgs = other.left, other.top, other.right, other.bottom
    self.__init__(*posArgs, **kwargs)

  @overload()
  def __init__(self, **kwargs) -> None:
    """Initialize the region with the default edges."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(0, 0, 0, 0, **kwargs)

  @overload(list)
  @overload(tuple)
  def __init__(self, vals: Any) -> None:
    """Initialize the region with the given edges."""
    if TYPE_CHECKING:
      assert callable(self.__init__)
    self.__init__(*vals)

  #  Functionality

  def _resolveOther(self, other: Any) -> Self:
    """Resolves other to a region. """
    cls = type(self)
    if isinstance(other, cls):
      return other
    try:
      return cls(other)
    except DispatchException:
      return NotImplemented

  def __contains__(self, other: Any) -> bool:
    """Can contain other points or regions. """
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return False
    if other.left < self.left:
      return False
    if other.top < self.top:
      return False
    if other.right > self.right:
      return False
    if other.bottom > self.bottom:
      return False
    return True

  def __add__(self, other: Any) -> Self:
    """Addition returns the region that contains both regions."""
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    left = min(self.left, other.left)
    top = min(self.top, other.top)
    right = max(self.right, other.right)
    bottom = max(self.bottom, other.bottom)
    return cls(left, top, right, bottom)

  def __sub__(self, other: Any) -> Self:
    """Subtraction returns the region that contains part of self, but no
    part of other."""
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    left = self.left
    top = self.top
    right = max(left, min(self.right, other.left))
    bottom = max(top, min(self.bottom, other.top))
    return cls(left, top, right, bottom)

  def __mul__(self, other: Any) -> Self:
    """Multiplication returns the region contained by both self and
    other. """
    cls = type(self)
    other = self._resolveOther(other)
    if other is NotImplemented:
      return NotImplemented
    left = max(self.left, other.left)
    top = max(self.top, other.top)
    right = max(left, min(self.right, other.right))
    bottom = max(top, min(self.bottom, other.bottom))
    return cls(left, top, right, bottom)

  def __matmul__(self, other: Any) -> Any:
    """Creates a map from this to the other region. """

  def __truediv__(self, other: Any) -> Self:
    """Not implemented"""
    return NotImplemented

  def __floordiv__(self, other: Any) -> Self:
    """Not implemented"""
    return NotImplemented

  def __mod__(self, other: Any) -> Self:
    """Not implemented"""
    return NotImplemented

  def __pow__(self, other: Any) -> Self:
    """Not implemented"""
    return NotImplemented

  def __str__(self, ) -> str:
    """String representation of the region."""
    infoSpec = """Region: %s -> %s"""
    topLeftStr = repr(self.topLeft)
    bottomRightStr = repr(self.bottomRight)
    return infoSpec % (topLeftStr, bottomRightStr)
