"""Alignum enumerates the different alignment types."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.attr import Field
from worktoy.keenum import KeeNum
from moreworktoy.keenum import auto

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class VAlignum(KeeNum):
  """VAlignum enumerates the different vertical alignment types."""

  TOP = auto(Qt.AlignmentFlag.AlignTop)
  CENTER = auto(Qt.AlignmentFlag.AlignVCenter)
  BOTTOM = auto(Qt.AlignmentFlag.AlignBottom)


class HAlignum(KeeNum):
  """HAlignum enumerates the different horizontal alignment types."""

  LEFT = auto(Qt.AlignmentFlag.AlignLeft)
  CENTER = auto(Qt.AlignmentFlag.AlignHCenter)
  RIGHT = auto(Qt.AlignmentFlag.AlignRight)


class Alignum(KeeNum):
  """Alignum enumerates the different alignment types."""

  horizontal = Field()
  vertical = Field()

  @horizontal.GET
  def _getHorizontal(self) -> HAlignum:
    """Get the horizontal alignment."""
    h = self.name.split('_')[-1]
    return HAlignum(h)

  @vertical.GET
  def _getVertical(self) -> VAlignum:
    """Get the vertical alignment."""
    v = self.name.split('_')[0]
    return VAlignum(v)

  TOP_LEFT = auto(VAlignum.TOP.val | HAlignum.LEFT.val)
  TOP_CENTER = auto(VAlignum.TOP.val | HAlignum.CENTER.val)
  TOP_RIGHT = auto(VAlignum.TOP.val | HAlignum.RIGHT.val)

  CENTER_LEFT = auto(VAlignum.CENTER.val | HAlignum.LEFT.val)
  CENTER_CENTER = auto(VAlignum.CENTER.val | HAlignum.CENTER.val)
  CENTER = auto(Qt.AlignmentFlag.AlignCenter)  # Equivalent to CENTER_CENTER
  CENTER_RIGHT = auto(VAlignum.CENTER.val | HAlignum.RIGHT.val)

  BOTTOM_LEFT = auto(VAlignum.BOTTOM.val | HAlignum.LEFT.val)
  BOTTOM_CENTER = auto(VAlignum.BOTTOM.val | HAlignum.CENTER.val)
  BOTTOM_RIGHT = auto(VAlignum.BOTTOM.val | HAlignum.RIGHT.val)
