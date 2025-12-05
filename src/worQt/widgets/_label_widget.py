"""
LabelWidget provides a widget showing a short text label. It is not
intended for multi-line text display.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPaintEvent, QPainter, QColor, QPen, QShowEvent
from PySide6.QtGui import QBrush

from worktoy.desc import Field, AttriBox
from worktoy.utilities import maybe

from . import BaseWidget
from ..core import Font
from ..nums import SizePolicy, SizeNum

if TYPE_CHECKING:
  from typing import Optional


class LabelWidget(BaseWidget):
  """
  LabelWidget provides a widget showing a short text label. It is not
  intended for multi-line text display.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_text__ = 'Welcome!'
  __fallback_policy__ = SizePolicy(SizeNum.MIN, SizeNum.MAX)

  #  Private Variables
  __inner_text__ = None
  __text_pen__ = None
  __background_brush__ = None

  #  Public Variables
  text = Field()
  font = AttriBox[Font]('courier', 18)
  pen = Field()
  backgroundBrush = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.GET
  def _getText(self, **kwargs) -> str:
    return maybe(self.__inner_text__, self.__fallback_text__)

  def _createPen(self, ) -> None:
    pen = QPen()
    pen.setColor(QColor(0, 0, 0))
    pen.setStyle(Qt.PenStyle.SolidLine)
    pen.setWidth(1)
    self.__text_pen__ = pen

  @pen.GET
  def _getPen(self, **kwargs) -> QPen:
    if self.__text_pen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createPen()
      return self._getPen(_recursion=True)
    return self.__text_pen__

  def _createBackgroundBrush(self, ) -> None:
    brush = QBrush()
    color = QColor(191, 191, 191)
    brush.setColor(color)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    self.__background_brush__ = brush

  @backgroundBrush.GET
  def _getBackgroundBrush(self, **kwargs) -> QBrush:
    if self.__background_brush__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBackgroundBrush()
      return self._getBackgroundBrush(_recursion=True)
    return self.__background_brush__

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

  def __init__(self, *args) -> None:
    argStr, args = self._parseText(*args)
    if argStr is not None:
      self.__inner_text__ = argStr
    BaseWidget.__init__(self, *args)
    self.__size_policy__ = SizePolicy(SizeNum.MIN, SizeNum.MAX)
    self.setSizePolicy(self.__size_policy__.Q)

  @staticmethod
  def _parseText(*args) -> tuple[Optional[str], list]:
    posArgs = [*reversed([*args, ]), ]
    out = []
    while posArgs:
      arg = posArgs.pop()
      if isinstance(arg, str):
        return arg, [*out, *posArgs, ]
      out.append(arg)
    return None, [*out, ]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  OPTIONAL METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showEvent(self, event: QShowEvent) -> None:
    self.setMinimumSize(self.font.boundSize(self.geometry(), self.text)),
    BaseWidget.showEvent(self, event)

  def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter()
    painter.begin(self)
    viewRect = painter.viewport()
    painter.setFont(self.font.Q)
    painter.setPen(self.pen)
    painter.setBrush(self.backgroundBrush)
    painter.drawRect(viewRect)
    flags = self.align.Q
    painter.drawText(viewRect, flags, self.text)
    painter.end()
