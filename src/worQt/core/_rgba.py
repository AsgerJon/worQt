"""
RGBA provides a color representation in the RGBA color space.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen, QBrush
from worktoy.desc import Field
from worktoy.ezdata import EZData

if TYPE_CHECKING:
  pass


class RGBA(EZData):
  """
  RGBA provides a color representation in the RGBA color space.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  red = 255
  green = 255
  blue = 255
  alpha = 255

  #  Virtual Variables
  Q = Field()
  pen = Field()
  brush = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQColor(self) -> QColor:
    color = QColor()
    color.setRed(self.red)
    color.setGreen(self.green)
    color.setBlue(self.blue)
    color.setAlpha(self.alpha)
    return color

  @pen.GET
  def _getPen(self) -> QPen:
    """Get the pen color."""
    pen = QPen()
    pen.setColor(self.Q)
    pen.setWidth(1)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setStyle(Qt.PenStyle.SolidLine)
    return pen

  @brush.GET
  def _getBrush(self) -> QBrush:
    """Get the brush color."""
    brush = QBrush()
    brush.setColor(self.Q)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    return brush
