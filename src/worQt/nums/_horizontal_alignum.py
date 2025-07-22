"""HorizontalAlignum enumerates horizontal alignments. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee


class HorizontalAlignum(KeeNum):
  """HorizontalAlignum enumerates horizontal alignments."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  LEFT = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignLeft)
  CENTER = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignHCenter)
  RIGHT = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignRight)
