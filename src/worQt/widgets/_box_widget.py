"""
BoxWidget provides a base widget implementing box-model painting.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QPaintEvent, QPainter
from worktoy.desc import AttriBox, Field

from ..core import BoxModel, RGBA
from . import BaseWidget

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self, Any


class BoxWidget(BaseWidget):
  """
  BoxWidget provides a base widget implementing box-model painting.
  It uses the BoxModel class to manage box model properties.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __content_rect__ = None

  #  Public Variables
  availableContentRect = Field()
  box = AttriBox[BoxModel]()
  marginColor = AttriBox[RGBA](0, 0, 0, 0, )
  borderColor = AttriBox[RGBA](0, 0, 0, 255)
  paddingColor = AttriBox[RGBA](255, 255, 255, 255, )

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @availableContentRect.GET
  def _getAvailableContentRect(self) -> QRect:
    return self.__content_rect__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter()
    painter.begin(self)
    marginRect = painter.viewport()
    borderRect = marginRect - self.box.margins
    paddingRect = borderRect - self.box.borders
    contentRect = paddingRect - self.box.paddings
    painter.setPen(self.emptyPen)
    painter.setBrush(self.marginColor.brush)
    rx, ry = self.box.marginsCorners
    painter.drawRoundedRect(marginRect, rx, ry)
    painter.setBrush(self.borderColor.brush)
    rx, ry = self.box.bordersCorners
    painter.drawRoundedRect(borderRect, rx, ry)
    painter.setBrush(self.paddingColor.brush)
    rx, ry = self.box.paddingsCorners
    painter.drawRoundedRect(paddingRect, rx, ry)
    painter.end()
    self.__content_rect__ = contentRect
