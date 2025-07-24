"""
LabelWidget subclasses the 'BoxWidget' and implements printing of text.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect
from PySide6.QtGui import QFont, QPaintEvent, QPainter, QColor
from PySide6.QtWidgets import QWidget, QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import Field, AttriBox
from worktoy.dispatch import Dispatcher
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException
from ..core import Font, RGBA

from . import BoxWidget
from ..nums import HorizontalAlignum as H
from ..nums import VerticalAlignum as V

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class LabelWidget(BoxWidget):
  """
  LabelWidget subclasses the 'BoxWidget' and implements printing of text.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_text__ = 'breh'

  #  Private Variables
  __private_text__ = None
  __private_font__ = None

  #  Public Variables
  text = Field()
  font = Field()
  textColor = AttriBox[RGBA](0, 0, 0, 255)
  textMarginColor = AttriBox[RGBA](0, 0, 0, 0)
  textBorderColor = AttriBox[RGBA](0, 0, 0, 255)
  textPaddingColor = AttriBox[RGBA](191, 191, 191, 255)

  #  Virtual Variables
  #  Growing from content rect by adding padding, border, and margin.
  contentRect = Field()  # The bounding rectangle of the text content.
  paddingRect = Field()  # Padding added to contentRect.
  borderRect = Field()  # Border added to paddingRect.
  marginRect = Field()  # Margin added to borderRect.

  #  Overloaded Functions
  __init__ = Dispatcher()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.GET
  def _getText(self) -> str:
    return maybe(self.__private_text__, self.__fallback_text__)

  def _createFont(self, ) -> None:
    """Creator for the font."""
    self.__private_font__ = Font()

  @font.GET
  def _getFont(self, **kwargs) -> Font:
    """
    Returns the font of the label.
    If no font is set, it returns a default font.
    """
    if self.__private_font__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createFont()
      return self._getFont(_recursion=True)
    if isinstance(self.__private_font__, Font):
      return self.__private_font__
    raise TypeException('__private_font__', self.__private_font__, Font, )

  @contentRect.GET
  def _getContentRect(self) -> QRect:
    return self.font.boundRect(self.availableContentRect, self.text)

  @paddingRect.GET
  def _getPaddingRect(self) -> QRect:
    return self.contentRect + self.box.paddings

  @borderRect.GET
  def _getBorderRect(self) -> QRect:
    return self.paddingRect + self.box.borders

  @marginRect.GET
  def _getMarginRect(self) -> QRect:
    return self.borderRect + self.box.margins

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.SET
  def _setText(self, value: str) -> None:
    self.__private_text__ = str(value)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @__init__.overload(str)
  def __init__(self, text: str) -> None:
    self.__private_text__ = str(text)

  @__init__.overload(str, RGBA, RGBA, RGBA)
  def __init__(self, text: str, *colors: RGBA) -> None:
    self.__private_text__ = str(text)
    self.textColor, self.paddingColor, self.borderColor = colors

  @__init__.overload(str, RGBA, RGBA)
  def __init__(self, text: str, *colors: RGBA) -> None:
    self.__private_text__ = str(text)
    self.textColor, self.paddingColor = colors

  @__init__.overload(str, RGBA)
  def __init__(self, text: str, color: RGBA) -> None:
    self.__private_text__ = str(text)
    self.textColor = color

  @__init__.overload(str, RGBA, RGBA, RGBA, Font)
  def __init__(self, text: str, *args) -> None:
    self.__private_text__ = str(text)
    self.textColor, self.paddingColor, self.borderColor, *_ = args
    self.__private_font__ = args[-1]

  @__init__.overload(str, RGBA, RGBA, Font)
  def __init__(self, text: str, *args) -> None:
    self.__private_text__ = str(text)
    self.textColor, self.paddingColor, self.__private_font__ = args

  @__init__.overload(str, RGBA, Font)
  def __init__(self, *args) -> None:
    self.__private_text__, self.textColor, self.__private_font__ = args

  @__init__.overload(str, Font)
  def __init__(self, text: str, font: Font) -> None:
    self.__private_text__ = str(text)
    self.__private_font__ = font

  @__init__.fallback
  def __init__(self, parent: QWidget, *args, **kwargs) -> None:
    if isinstance(parent, QWidget):
      BoxWidget.__init__(self, parent)
    else:
      BoxWidget.__init__(self, )
    self.__init__(*args, **kwargs)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, event: QPaintEvent) -> None:
    BoxWidget.paintEvent(self, event)
    painter = QPainter()
    painter.begin(self)
    painter.setPen(self.emptyPen)
    painter.setBrush(self.textMarginColor.brush)
    rx, ry = self.box.marginsCorners
    painter.drawRoundedRect(self.marginRect, rx, ry)
    painter.setBrush(self.textBorderColor.brush)
    rx, ry = self.box.marginsCorners
    painter.drawRoundedRect(self.borderRect, rx, ry)
    painter.setBrush(self.textPaddingColor.brush)
    rx, ry = self.box.paddingsCorners
    painter.drawRoundedRect(self.paddingRect, rx, ry)
    painter.setFont(self.font.Q)
    painter.setPen(self.textColor.pen)
    painter.setBrush(self.emptyBrush)
    painter.drawText(self.contentRect, self.text)
