"""
EdgeNum enumerates the four edges of a rectangular context aligned with
horizontal and vertical axes. The edges are enumerated in clockwise order
starting from the left side. The edges are named 'left', 'top', 'right',
and 'bottom'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EdgeNum(KeeNum):
  """
  EdgeNum enumerates the four edges of a rectangular context aligned with
  horizontal and vertical axes. The edges are enumerated in clockwise order
  starting from the left side. The edges are named 'left', 'top', 'right',
  and 'bottom'.
  """

  LEFT = Kee[int](0)
  TOP = Kee[int](1)
  RIGHT = Kee[int](2)
  BOTTOM = Kee[int](3)
