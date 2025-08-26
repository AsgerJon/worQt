"""
LabelWidget subclasses the 'BoxWidget' and implements printing of text.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen, QBrush, QFontMetrics
from worktoy.desc import Field, AttriBox
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException

from ..core import Font, RGBA
from . import BoxWidget
from ..geometry import Size, Rect, Margins
from ..nums import Alignum

if TYPE_CHECKING:  # pragma: no cover
  pass


class LabelWidget(BoxWidget):
  """
  LabelWidget subclasses the 'BoxWidget' and implements printing of text.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables
  __fallback_text__ = 'Label'
  __fallback_alignment__ = Alignum.CENTER
  __fallback_color__ = RGBA(0, 0, 0, 255)
  __fallback_shadow__ = RGBA(225, 225, 225, 255)

  #  Private Variables
  __private_text__ = None
  __private_font__ = None
  __alignment_flag__ = None
  __text_color__ = None
  __shadow_color__ = None

  #  Public Variables
  opacity = AttriBox[float](1.0, )
  text = Field()
  font = Field()
  alignmentFlag = Field()
  textColor = Field()
  shadowColor = Field()

  #  Virtual Variables
  textPen = Field()
  shadowBrush = Field()
  textRect = Field()
  shadowRect = Field()
  boundingSize = Field()
  boundingRect = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @textColor.GET
  def _getTextColor(self) -> RGBA:
    return maybe(self.__text_color__, self.__fallback_color__)

  @shadowColor.GET
  def _getShadowColor(self) -> RGBA:
    return maybe(self.__shadow_color__, self.__fallback_shadow__)

  @textPen.GET
  def _getTextPen(self) -> QPen:
    pen = QPen()
    color = self.textColor.Q
    color.setAlphaF(self.opacity)
    pen.setColor(color)
    pen.setWidth(1)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    pen.setStyle(Qt.PenStyle.SolidLine)
    return pen

  @shadowBrush.GET
  def _getShadowBrush(self) -> QBrush:
    brush = QBrush()
    color = self.shadowColor.Q
    brush.setColor(color)
    brush.setStyle(Qt.BrushStyle.SolidPattern)
    return brush

  @boundingSize.GET
  def _getBoundingSize(self) -> Size:
    fontMetrics = QFontMetrics(self.font.Q)
    rect = fontMetrics.boundingRect(self.text)
    return Size(rect.width(), rect.height())

  @boundingRect.GET
  def _getBoundingRect(self) -> Rect:
    return Rect(self.boundingSize, )

  @textRect.GET
  def _getTextRect(self) -> Rect:
    """
    Returns the rectangle where the text will be drawn.
    It is aligned to the contentRect with the alignmentFlag.
    """
    rect = self.boundingRect
    return rect.align(self.contentRect, self.alignmentFlag)

  @shadowRect.GET
  def _getShadowRect(self) -> Rect:
    rect = self.boundingRect + Margins(2, 0, 2, 0)
    return rect.align(self.contentRect, self.alignmentFlag)

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

  @alignmentFlag.GET
  def _getAlignmentFlag(self) -> Alignum:
    return maybe(self.__alignment_flag__, self.__fallback_alignment__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @text.SET
  def _setText(self, value: str) -> None:
    if self.__private_text__ != value:
      self.__private_text__ = str(value)
      self.update()

  @font.SET
  def _setFont(self, value: Font) -> None:
    if not isinstance(value, Font):
      raise TypeException('__private_font__', value, Font)
    self.__private_font__ = value
    self.update()

  @alignmentFlag.SET
  def _setAlignmentFlag(self, value: Alignum) -> None:
    if not isinstance(value, Alignum):
      raise TypeException('__alignment_flag__', value, Alignum)
    self.__alignment_flag__ = value
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    BoxWidget.__init__(self, *args, **kwargs)
    self.setMouseTracking(True)
    textArg = [arg for arg in args if isinstance(arg, str)] or [None, ]
    fontArg = [arg for arg in args if isinstance(arg, Font)] or [None, ]
    if textArg[0] is not None:
      self.text = textArg[0]
    if fontArg[0] is not None:
      self.font = fontArg[0]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintMeLike(self, painter: QPainter, **kwargs, ) -> None:
    painter.setFont(self.font.Q)
    painter.setPen(self.textPen)
    painter.setBrush(self.shadowBrush)
    flags = Qt.AlignmentFlag.AlignCenter
    painter.drawRoundedRect(self.shadowRect.Q, 2, 2)
    painter.drawText(self.textRect.Q, flags, self.text)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
