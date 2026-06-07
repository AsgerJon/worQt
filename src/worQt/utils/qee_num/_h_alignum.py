"""
HAlignum enumerates horizontal alignments.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

QLEFT = Qt.AlignmentFlag.AlignLeft
QHCENTER = Qt.AlignmentFlag.AlignHCenter
QRIGHT = Qt.AlignmentFlag.AlignRight


class HAlignum(KeeNum):
  """
  HAlignum enumerates horizontal alignments.
  """

  LEFT = Kee[Qt.AlignmentFlag](QLEFT)
  CENTER = Kee[Qt.AlignmentFlag](QHCENTER)
  RIGHT = Kee[Qt.AlignmentFlag](QRIGHT)
