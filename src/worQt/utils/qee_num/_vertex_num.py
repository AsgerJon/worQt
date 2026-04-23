"""
VertexNum enumerates the vertices of a rectangle.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class VertexNum(KeeNum):
  """
  VertexNum enumerates the vertices of a rectangle.
  """

  TOP_LEFT = Kee[int](0)
  TOP_RIGHT = Kee[int](1)
  BOTTOM_RIGHT = Kee[int](2)
  BOTTOM_LEFT = Kee[int](3)
