"""
VAlignum enumerates vertical alignments.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

QTOP = Qt.AlignmentFlag.AlignTop
QVCENTER = Qt.AlignmentFlag.AlignVCenter
QBOTTOM = Qt.AlignmentFlag.AlignBottom


class VAlignum(KeeNum):
  """
  VAlignum enumerates vertical alignments.
  """

  TOP = Kee[Qt.AlignmentFlag](QTOP)
  CENTER = Kee[Qt.AlignmentFlag](QVCENTER)
  BOTTOM = Kee[Qt.AlignmentFlag](QBOTTOM)
