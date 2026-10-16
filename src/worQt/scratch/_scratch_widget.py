"""
ScratchWidget provides the sample widget.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRect, QSize, QPoint
from PySide6.QtGui import QPaintEvent, QPainter, QBrush, QColor, QPen
from worktoy.desc import AttriBox, Field
from worktoy.waitaminute import TypeException

from ..widgets import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, Union, TypeAlias, Type


class ScratchWidget(BaseWidget):
  """
  ScratchWidget provides the sample widget.
  """

  __fallback_background__: tuple[int, int, int, int] = 255, 255, 255, 255
  __fallback_line_color__: tuple[int, int, int, int] = 0, 0, 0, 255
  __fallback_line_width__: int = 1

  __background_brush__: Optional[QBrush] = None
  __background_color__: Optional[QColor] = None
  __line_color__: Optional[QColor] = None
  __line_width__: Optional[int] = None
  __line_pen__: Optional[QPen] = None

  minWidth = AttriBox[int](32)
  minHeight = AttriBox[int](32)
  backgroundColor: Field[QColor] = Field()
  backgroundBrush: Field[QBrush] = Field()
  lineColor: Field[QColor] = Field()
  lineWidth: Field[int] = Field()
  linePen: Field[QPen] = Field()

  def _createBackgroundColor(self, ) -> None:
    self.__background_color__ = QColor(*self.__fallback_background__)

  @backgroundColor.GET
  def _getBackgroundColor(self, **kwargs) -> QColor:
    if self.__background_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBackgroundColor()
      return self._getBackgroundColor(_recursion=True)
    if isinstance(self.__background_color__, QColor):
      return self.__background_color__
    name, value = '__background_color__', self.__background_color__
    raise TypeException(name, value, QColor)

  def _createBackgroundBrush(self, ) -> None:
    brush: QBrush = QBrush()
    QBrush.setColor(brush, self.backgroundColor)
    QBrush.setStyle(brush, Qt.BrushStyle.SolidPattern)
    self.__background_brush__ = brush

  @backgroundBrush.GET
  def _getBackgroundBrush(self, **kwargs) -> QBrush:
    if self.__background_brush__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createBackgroundBrush()
      return self._getBackgroundBrush(_recursion=True)
    if isinstance(self.__background_brush__, QBrush):
      return self.__background_brush__
    name, value = '__background_brush__', self.__background_brush__
    raise TypeException(name, value, QBrush)

  def _createLineColor(self, ) -> None:
    self.__line_color__ = QColor(*self.__fallback_line_color__)

  @lineColor.GET
  def _getLineColor(self, **kwargs) -> QColor:
    if self.__line_color__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createLineColor()
      return self._getLineColor(_recursion=True)
    if isinstance(self.__line_color__, QColor):
      return self.__line_color__
    name, value = '__line_color__', self.__line_color__
    raise TypeException(name, value, QColor)

  def _createLineWidth(self, ) -> None:
    self.__line_width__ = self.__fallback_line_width__

  @lineWidth.GET
  def _getLineWidth(self, **kwargs) -> int:
    if self.__line_width__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createLineWidth()
      return self._getLineWidth(_recursion=True)
    if isinstance(self.__line_width__, int):
      return self.__line_width__
    name, value = '__line_width__', self.__line_width__
    raise TypeException(name, value, int)

  def _createLinePen(self, ) -> None:
    pen: QPen = QPen()
    QPen.setColor(pen, self.lineColor)
    QPen.setWidth(pen, self.lineWidth)
    self.__line_pen__ = pen

  @linePen.GET
  def _getLinePen(self, **kwargs) -> QPen:
    if self.__line_pen__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createLinePen()
      return self._getLinePen(_recursion=True)
    if isinstance(self.__line_pen__, QPen):
      return self.__line_pen__
    name, value = '__line_pen__', self.__line_pen__
    raise TypeException(name, value, QPen)

  def initUI(self) -> None:
    raise NotImplementedError

  def paintEvent(self, event: QPaintEvent) -> None:
    painter: QPainter = QPainter()
    painter.begin(self)
    viewRect: QRect = QPainter.viewport(painter)
    viewCenter: QPoint = QRect.center(viewRect, )
    viewWidth: int = QRect.width(viewRect)
    viewHeight: int = QRect.height(viewRect)
    #  Bordered
    borderedWidth: int = viewWidth - 8
    borderedHeight: int = viewHeight - 8
    borderedSize: QSize = QSize(borderedWidth, borderedHeight)
    borderedRect: QRect = QRect(QPoint(0, 0), borderedSize)
    #  Padded
    paddedWidth: int = borderedWidth - 2
    paddedHeight: int = borderedHeight - 2
    paddedSize: QSize = QSize(paddedWidth, paddedHeight)
    paddedRect: QRect = QRect(QPoint(0, 0), paddedSize)
    #  Content
    contentWidth: int = paddedWidth - 6
    contentHeight: int = paddedHeight - 6
    contentSize: QSize = QSize(contentWidth, contentHeight)
    contentRect: QRect = QRect(QPoint(0, 0), contentSize)
    #  Alignment
    QRect.moveCenter(borderedRect, viewCenter)
    QRect.moveCenter(paddedRect, viewCenter)
    QRect.moveCenter(contentRect, viewCenter)
