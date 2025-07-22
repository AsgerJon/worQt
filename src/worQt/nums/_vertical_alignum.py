"""VerticalAlignum enumerates vertical alignments. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee


class VerticalAlignum(KeeNum):
  """VerticalAlignum enumerates vertical alignments."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations

  TOP = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignTop)
  CENTER = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignVCenter)
  BOTTOM = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignBottom)
