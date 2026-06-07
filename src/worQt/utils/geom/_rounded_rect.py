"""
RoundedRect subclasses 'Rect' and adds corner radii ('horizontalRadius' and
'verticalRadius', aliased 'hr'/'vr'). It inherits every 'Rect' constructor
and adds one taking a rect plus the two radii.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Alias
from worktoy.dispatch import overload

from ._rect import Rect

if TYPE_CHECKING:  # pragma: no cover
  pass


class RoundedRect(Rect):
  """A 'Rect' with horizontal and vertical corner radii."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  horizontalRadius = AttriBox[int](0)
  verticalRadius = AttriBox[int](0)
  hr = Alias('horizontalRadius')
  vr = Alias('verticalRadius')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Rect, int, int)
  def __init__(self, rect: Rect, hRadius: int, vRadius: int) -> None:
    self.left, self.top = rect.left, rect.top
    self.right, self.bottom = rect.right, rect.bottom
    self.horizontalRadius = hRadius
    self.verticalRadius = vRadius
