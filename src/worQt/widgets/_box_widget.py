"""
BoxWidget provides a base widget implementing box-model painting.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QPaintEvent, QPainter
from worktoy.desc import AttriBox, Field
from worktoy.utilities import maybe

from ..core import RGBA
from ..desQt.pens import EmptyPen, EmptyBrush
from ..geometry import BoxModel, Rect, Margins

from . import BaseWidget

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  pass


class BoxWidget(BaseWidget):
  """
  BoxWidget provides a base widget implementing box-model painting.
  It uses the BoxModel class to manage box model properties.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  emptyPen = EmptyPen()
  emptyBrush = EmptyBrush()

  #  Fallback Variables
  __fallback_margin_color__ = RGBA(255, 255, 255, 255)
  __fallback_border_color__ = RGBA(0, 0, 0, 255)
  __fallback_padding_color__ = RGBA(255, 255, 255, 255)
  __fallback_margins__ = Margins(4, 4, 4, 4, )
  __fallback_borders__ = Margins(0, 0, 0, 0, )
  __fallback_paddings__ = Margins(2, 2, 2, 2, )

  #  Private Variables
  __margin_rect__: Rect = None
  __box_model__ = None
  __box_margins__ = None
  __box_borders__ = None
  __box_paddings__ = None
  __margin_color__ = None
  __border_color__ = None
  __padding_color__ = None

  #  Public Variables
  box = Field()
  marginRect = Field()
  boxMargins = Field()
  boxBorders = Field()
  boxPaddings = Field()
  marginColor = Field()
  borderColor = Field()
  paddingColor = Field()

  #  Virtual Variables
  borderRect = Field()
  paddingRect = Field()
  contentRect = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _createBox(self) -> None:
    self.__box_model__ = BoxModel()

  @boxMargins.GET
  def _getBoxMargins(self) -> Margins:
    return maybe(self.__box_margins__, self.__fallback_margins__)

  @boxBorders.GET
  def _getBoxBorders(self) -> Margins:
    return maybe(self.__box_borders__, self.__fallback_borders__)

  @boxPaddings.GET
  def _getBoxPaddings(self) -> Margins:
    return maybe(self.__box_paddings__, self.__fallback_paddings__)

  @marginColor.GET
  def _getMarginColor(self) -> RGBA:
    return maybe(self.__margin_color__, self.__fallback_margin_color__)

  @borderColor.GET
  def _getBorderColor(self) -> RGBA:
    return maybe(self.__border_color__, self.__fallback_border_color__)

  @paddingColor.GET
  def _getPaddingColor(self) -> RGBA:
    return maybe(self.__padding_color__, self.__fallback_padding_color__)

  @box.GET
  def _getBox(self, **kwargs) -> BoxModel:
    if self.__box_model__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBox()
      return self._getBox(_recursion=True)
    return self.__box_model__

  @marginRect.GET
  def _getMarginRect(self, **kwargs) -> Rect:
    if self.__margin_rect__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__margin_rect__ = Rect(self.geometry(), )
      return self._getMarginRect(_recursion=True)
    return self.__margin_rect__

  @borderRect.GET
  def _getBorderRect(self, **kwargs) -> Rect:
    return self.marginRect - self.boxMargins

  @paddingRect.GET
  def _getPaddingRect(self, **kwargs) -> Rect:
    return self.borderRect - self.boxBorders

  @contentRect.GET
  def _getContentRect(self, **kwargs) -> Rect:
    return self.paddingRect - self.boxPaddings

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

  def paintMeLike(self, painter: QPainter, **kwargs, ) -> None:
    """
    Subclasses should implement this method to specify the painting. The
    'QPainter' object passed must not be ended. It should paint inside the
    'Rect' object specified by the 'contentRect' property of this widget.
    Please note that prior to this method being called, the box model
    graphics have already been painted. The widget painter should
    generally fill this content rectangle.

    The default implementation is a no-op
    """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paintEvent(self, event: QPaintEvent) -> None:
    BaseWidget.paintEvent(self, event)
    painter = QPainter()
    painter.begin(self)
    self.__margin_rect__ = Rect(painter.viewport())
    painter.setPen(self.emptyPen)
    painter.setBrush(self.marginColor.brush)
    rx, ry = self.box.marginsCorners
    painter.drawRoundedRect(self.marginRect.Q, rx, ry)
    painter.setBrush(self.borderColor.brush)
    rx, ry = self.box.bordersCorners
    painter.drawRoundedRect(self.borderRect.Q, rx, ry)
    painter.setBrush(self.paddingColor.brush)
    rx, ry = self.box.paddingsCorners
    painter.drawRoundedRect(self.paddingRect.Q, rx, ry)
    self.paintMeLike(painter, )
    painter.end()
