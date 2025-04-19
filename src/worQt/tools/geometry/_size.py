"""Size class subclasses Plane and provides a size in 2D space. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import Field

from moreworktoy.attr import Alias
from . import Plane

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

from typing import Self


class Size(Plane):
  """Size class subclasses Plane and provides a size in 2D space."""

  aspectRatio = Field()
  width = Field()
  height = Field()

  @width.GET
  def _getWidth(self) -> float:
    """Get the width of the size."""
    return abs(self.r0)

  @height.GET
  def _getHeight(self) -> float:
    """Get the height of the size."""
    return abs(self.r1)

  @aspectRatio.GET
  def _getAspectRatio(self) -> float:
    """Get the aspect ratio of the size."""
    if not self.height:
      raise ZeroDivisionError
    return self.width / self.height

  def fit(self, other: Self) -> Self:
    """Creates a new size preserving the aspect ratio of 'self', whilst
    being strictly smaller than 'other'."""
    if TYPE_CHECKING:
      assert isinstance(other.width, float)
      assert isinstance(other.height, float)
      assert isinstance(self.width, float)
      assert isinstance(self.height, float)

    hScale, wScale = other.height / self.height, other.width / self.width
    h0, w0 = self.height * hScale, self.width * hScale
    h1, w1 = self.height * wScale, self.width * wScale
    if h0 <= other.height and w0 <= other.width:
      return Size(self.width * hScale, self.height * hScale)
    if h1 <= other.height and w1 <= other.width:
      return Size(self.width * wScale, self.height * wScale)
    e = """Unable to fit '%s' into '%s'""" % (self, other)
    raise RuntimeError(e)
