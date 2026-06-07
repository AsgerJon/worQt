"""
BoxNum enumerates the rectangular members of a box model layout.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class BoxNum(KeeNum):
  """
  BoxNum enumerates the rectangular members of a box model layout.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ENUMERATIONS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  MARGIN = Kee[int](0)
  BORDER = Kee[int](1)
  PADDING = Kee[int](2)
  CONTENT = Kee[int](3)
