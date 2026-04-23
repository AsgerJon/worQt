"""
RoundedRect subclasses Rect and adds corner radii.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic
from worktoy.desc import Alias
from worktoy.dispatch import overload

from . import Rect
from .euclid import Dimension

if TYPE_CHECKING:  # pragma: no cover
  pass


class RoundedRect(Rect):
  """
  RoundedRect subclasses Rect and adds corner radii.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __h_keys__ = 'hRadius', 'h_radius', 'x_radius', 'horizontalRadius', 'hr'
  __v_keys__ = 'vRadius', 'v_radius', 'y_radius', 'verticalRadius', 'vr'

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  horizontalRadius = Dimension(int, 0, *__h_keys__)
  verticalRadius = Dimension(int, 0, *__v_keys__)
  hr = Alias('horizontalRadius')
  vr = Alias('verticalRadius')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Rect, int, int)
  def __init__(self, rect: Rect, h_radius: int, v_radius: int) -> None:
    super().__init__(rect.Q, )
    self.horizontalRadius = h_radius
    self.verticalRadius = v_radius
