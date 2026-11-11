"""
EdgeNum enumerates the edges of a rectangular disk.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.desc import Field
from worktoy.keenum import Kee, KeeNum


class EdgeNum(KeeNum):
  """
  EdgeNum enumerates the four edges of a rectangular disk, each resolved
  by its name: 'EdgeNum('bottom')'. The bottom and the top are
  'horizontal', running along x; the left and the right run along y.
  'outward' is the unit vector pointing out of the disk across the
  edge, with y upwards.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  BOTTOM: Kee[str] = Kee[str]('bottom')
  RIGHT: Kee[str] = Kee[str]('right')
  TOP: Kee[str] = Kee[str]('top')
  LEFT: Kee[str] = Kee[str]('left')

  #  Virtual Variables
  horizontal: Field[bool] = Field()
  outward: Field[tuple[float, float]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @horizontal.GET
  def _getHorizontal(self, ) -> bool:
    """The 'horizontal' getter tells whether the edge runs along x."""
    cls = type(self)
    return True if self in (cls.BOTTOM, cls.TOP) else False

  @outward.GET
  def _getOutward(self, ) -> tuple[float, float]:
    """The 'outward' getter returns the unit vector out of the disk across
    the edge."""
    cls = type(self)
    if self is cls.BOTTOM:
      return 0.0, -1.0
    if self is cls.RIGHT:
      return 1.0, 0.0
    if self is cls.TOP:
      return 0.0, 1.0
    return -1.0, 0.0
