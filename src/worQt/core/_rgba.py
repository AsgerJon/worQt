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
from worktoy.dispatch import overload
from worktoy.ezdata import EZData
from worktoy.utilities import maybe

if TYPE_CHECKING:
  pass


class RGBA(EZData):
  """
  RGBA provides a color representation in the RGBA color space.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_red__ = 255
  __fallback_green__ = 255
  __fallback_blue__ = 255
  __fallback_alpha__ = 255

  #  Private Variables
  __private_red__ = None
  __private_green__ = None
  __private_blue__ = None
  __private_alpha__ = None

  #  Virtual Variables
  Q = Field()
  pen = Field()
  brush = Field()
  red = Field()
  green = Field()
  blue = Field()
  alpha = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @red.GET
  def _getRed(self) -> int:
    """Get the red component of the color."""
    return maybe(self.__private_red__, self.__fallback_red__)

  @green.GET
  def _getGreen(self) -> int:
    """Get the green component of the color."""
    return maybe(self.__private_green__, self.__fallback_green__)

  @blue.GET
  def _getBlue(self) -> int:
    """Get the blue component of the color."""
    return maybe(self.__private_blue__, self.__fallback_blue__)

  @alpha.GET
  def _getAlpha(self) -> int:
    """Get the alpha component of the color."""
    return maybe(self.__private_alpha__, self.__fallback_alpha__)

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

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @red.SET
  def _setRed(self, value: int) -> None:
    """
    Set the red component of the color.
    :param value: The red component (0-255).
    """
    if not isinstance(value, int) or not (0 <= value <= 255):
      raise ValueError("Red value must be an integer between 0 and 255.")
    self.__private_red__ = value

  @green.SET
  def _setGreen(self, value: int) -> None:
    """
    Set the green component of the color.
    :param value: The green component (0-255).
    """
    if not isinstance(value, int) or not (0 <= value <= 255):
      raise ValueError("Green value must be an integer between 0 and 255.")
    self.__private_green__ = value

  @blue.SET
  def _setBlue(self, value: int) -> None:
    """
    Set the blue component of the color.
    :param value: The blue component (0-255).
    """
    if not isinstance(value, int) or not (0 <= value <= 255):
      raise ValueError("Blue value must be an integer between 0 and 255.")
    self.__private_blue__ = value

  @alpha.SET
  def _setAlpha(self, value: int) -> None:
    """
    Set the alpha component of the color.
    :param value: The alpha component (0-255).
    """
    if not isinstance(value, int) or not (0 <= value <= 255):
      raise ValueError("Alpha value must be an integer between 0 and 255.")
    self.__private_alpha__ = value

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(int, int, int, int)
  def __init__(self, *args, ) -> None:
    self.__private_red__ = args[0]
    self.__private_green__ = args[1]
    self.__private_blue__ = args[2]
    self.__private_alpha__ = args[3]

  @overload(int, int, int)
  def __init__(self, *args, ) -> None:
    self.__private_red__ = args[0]
    self.__private_green__ = args[1]
    self.__private_blue__ = args[2]
    self.__private_alpha__ = self.__fallback_alpha__

  @overload(int, int)
  def __init__(self, *args, ) -> None:
    self.__private_red__ = args[0]
    self.__private_green__ = self.__fallback_green__
    self.__private_blue__ = self.__fallback_blue__
    self.__private_alpha__ = args[1]

  @overload(int)
  def __init__(self, *args, ) -> None:
    self.__private_red__ = args[0]
    self.__private_green__ = args[0]
    self.__private_blue__ = args[0]
    self.__private_alpha__ = self.__fallback_alpha__

  @overload()
  def __init__(self, ) -> None:
    pass

  @overload(QColor)
  def __init__(self, color: QColor) -> None:
    """Initializes the RGBA with a QColor object."""
    self.__private_red__ = color.red()
    self.__private_green__ = color.green()
    self.__private_blue__ = color.blue()
    self.__private_alpha__ = color.alpha()
