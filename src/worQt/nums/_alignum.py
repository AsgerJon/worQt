"""
Alignum enumerates alignments.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worktoy.keenum import KeeNum, Kee
from worktoy.desc import Field

from . import HorizontalAlignum as H
from . import VerticalAlignum as V


class Alignum(KeeNum):
  """Alignum enumerates alignments."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  horizontal = Field()
  vertical = Field()

  #  Enumerations

  TOP_LEFT = Kee[Qt.AlignmentFlag](H.LEFT.value | V.TOP.value)
  TOP_CENTER = Kee[Qt.AlignmentFlag](H.CENTER.value | V.TOP.value)
  TOP_RIGHT = Kee[Qt.AlignmentFlag](H.RIGHT.value | V.TOP.value)

  CENTER_LEFT = Kee[Qt.AlignmentFlag](H.LEFT.value | V.CENTER.value)
  CENTER = Kee[Qt.AlignmentFlag](Qt.AlignmentFlag.AlignCenter)
  CENTER_RIGHT = Kee[Qt.AlignmentFlag](H.RIGHT.value | V.CENTER.value)

  BOTTOM_LEFT = Kee[Qt.AlignmentFlag](H.LEFT.value | V.BOTTOM.value)
  BOTTOM_CENTER = Kee[Qt.AlignmentFlag](H.CENTER.value | V.BOTTOM.value)
  BOTTOM_RIGHT = Kee[Qt.AlignmentFlag](H.RIGHT.value | V.BOTTOM.value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @horizontal.GET
  def _getHorizontal(self) -> H:
    """Get the horizontal alignment."""
    if 'LEFT' in self.name:
      return H.LEFT
    if 'RIGHT' in self.name:
      return H.RIGHT
    return H.CENTER

  @vertical.GET
  def _getVertical(self) -> V:
    """Get the vertical alignment."""
    if 'TOP' in self.name:
      return V.TOP
    if 'BOTTOM' in self.name:
      return V.BOTTOM
    return V.CENTER
