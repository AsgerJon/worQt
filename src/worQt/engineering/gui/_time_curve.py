"""
TimeCurve subclasses 'PaintedWidget' and plots a few things against
time, the last stretch of them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QSize
from PySide6.QtGui import QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ...paint_ops import AbstractPaintOp, PaintBoxModel
from ...utils import WFont, Color
from ...utils.font_nums import GenericFamilyNum, FontWeightNum
from ...utils.geom import InSets, Size
from ...widgets import PaintedWidget
from ._nice_above import niceAbove, niceSpan

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter
  from ...utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_TICK = 5.0  # pixels: how long a tick is

Series = tuple[str, Color, list[tuple[float, float]]]


class PaintTimeCurve(AbstractPaintOp):
  """
  PaintTimeCurve subclasses 'AbstractPaintOp' and paints a 'TimeCurve':
  the title, what each colour is, the axes with their gridlines, ticks
  and names, and the curves.
  """

  #  Annotations
  widget: TimeCurve

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the plot."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = widget.plotRect()
    painter.setFont(widget.titleFont)
    painter.setPen(widget.titleFont.color.Q)
    painter.drawText(QRectF(box.left(), 6.0, box.width(), 20.0), _LEFT,
                     widget.title)
    self._paintKey(painter)
    self._paintAxes(painter)
    for _, color, line in widget.lines():
      if len(line) > 1:
        painter.setPen(QPen(color.Q, 1.6))
        painter.drawPolyline(QPolygonF(line))
    return rect

  def _paintKey(self, painter: WPainter) -> None:
    """What each colour is, in its colour, under the title; or the
    words, if there is nothing plotted."""
    widget = self.widget
    box = widget.plotRect()
    painter.setFont(widget.font)
    left = box.left()
    if not widget.series:
      painter.setPen(widget.textColor.Q)
      painter.drawText(QRectF(left, 28.0, box.width(), 16.0), _LEFT,
                       widget.words)
      return
    metrics = widget.font.metrics
    for name, color, _ in widget.series:
      painter.setPen(color.Q)
      painter.drawText(QRectF(left, 28.0, 200.0, 16.0), _LEFT, name)
      left += metrics.horizontalAdvance(name) + 14

  def _paintAxes(self, painter: WPainter) -> None:
    """The gridlines and ticks, the axes, the line through nought, and
    their names."""
    widget = self.widget
    box = widget.plotRect()
    start, end, along = widget.timeAxis()
    bottom, top, up = widget.valueAxis()
    grid = QPen(widget.gridColor.Q, 1.0)
    axis = QPen(widget.axisColor.Q, 1.0)
    painter.setFont(widget.font)
    for index in range(int(round((end - start) / along)) + 1):
      value = start + index * along
      x = widget.toScreen(value, 0.0).x()
      painter.setPen(grid)
      painter.drawLine(QLineF(x, box.top(), x, box.bottom()))
      painter.setPen(axis)
      painter.drawLine(QLineF(x, box.bottom(), x, box.bottom() + _TICK))
      label = QRectF(x - 30.0, box.bottom() + _TICK, 60.0, 16.0)
      shown = round(value * widget.timeScale()[0], 6)
      painter.drawText(label, _CENTER, '%g' % shown)
    for index in range(int(round((top - bottom) / up)) + 1):
      value = bottom + index * up
      y = widget.toScreen(start, value).y()
      painter.setPen(grid)
      painter.drawLine(QLineF(box.left(), y, box.right(), y))
      painter.setPen(axis)
      painter.drawLine(QLineF(box.left() - _TICK, y, box.left(), y))
      label = QRectF(box.left() - 60.0, y - 8.0, 60.0 - 2 * _TICK, 16.0)
      painter.drawText(label, _RIGHT, '%g' % round(value, 6))
    painter.setPen(axis)
    nought = widget.toScreen(start, 0.0).y()
    painter.drawLine(QLineF(box.left(), nought, box.right(), nought))
    painter.drawLine(QLineF(box.left(), box.top(), box.left(),
                            box.bottom()))
    painter.setPen(widget.textColor.Q)
    under = QRectF(box.left(), box.bottom() + 22.0, box.width(), 16.0)
    painter.drawText(under, _CENTER, 'time %s' % widget.timeScale()[1])
    painter.drawText(QRectF(4.0, box.top() - 22.0, 56.0, 14.0), _LEFT,
                     widget.unit)


class TimeCurve(PaintedWidget):
  """
  TimeCurve subclasses 'PaintedWidget' and plots a few things against
  time: 'series', each a name, a colour and its values at times, the
  last 'window' seconds of them, twenty unless set, the time scrolling
  on, in milliseconds when the window is shorter than a second; its
  'title' above and, beside the value axis, their 'unit'. With nothing
  to plot, it says 'words' instead. 'showSeries' shows them.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_axis_color__ = Color(140, 144, 152)
  __fallback_grid_color__ = Color(48, 50, 55)
  __fallback_text_color__ = Color(170, 174, 182)
  __fallback_plot_margins__ = (64.0, 54.0, 24.0, 44.0)  # l, t, r, b
  __fallback_window__ = 20.0  # s of time shown, unless set
  __fallback_least_value__ = 1.0  # the value axis reaches at least this

  #  Private Variables
  __curve_title__: str = ''
  __curve_words__: str = ''
  __curve_unit__: str = ''
  __curve_series__: tuple = ()
  __curve_window__: float | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  curveOp = PaintTimeCurve()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )
  titleFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      12,
      Color(212, 212, 212),
  )

  #  Virtual Variables
  title: Field[str] = Field()
  words: Field[str] = Field()
  unit: Field[str] = Field()
  series: Field[tuple[Series, ...]] = Field()
  window: Field[float] = Field()
  axisColor: Field[Color] = Field()
  gridColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @title.GET
  def _getTitle(self, ) -> str:
    """The 'title' getter returns what the plot is of."""
    return self.__curve_title__

  @words.GET
  def _getWords(self, ) -> str:
    """The 'words' getter returns what the plot says with nothing to
    plot."""
    return self.__curve_words__

  @unit.GET
  def _getUnit(self, ) -> str:
    """The 'unit' getter returns the unit of the values."""
    return self.__curve_unit__

  @series.GET
  def _getSeries(self, ) -> tuple[Series, ...]:
    """The 'series' getter returns what is plotted: each a name, a
    colour and its values at times."""
    return self.__curve_series__

  @window.GET
  def _getWindow(self, ) -> float:
    """The 'window' getter returns how many seconds of time are
    shown."""
    if self.__curve_window__ is None:
      return self.__fallback_window__
    return self.__curve_window__

  @axisColor.GET
  def _getAxisColor(self, ) -> Color:
    return self.__fallback_axis_color__

  @gridColor.GET
  def _getGridColor(self, ) -> Color:
    return self.__fallback_grid_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @window.SET
  def _setWindow(self, seconds: float) -> None:
    """The 'window' setter shows the last 'seconds' of time."""
    if not seconds > 0:
      raise ValueError('a window of time is above nought')
    self.__curve_window__ = float(seconds)
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(440, 280)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(300, 200)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showSeries(self, title: str, unit: str, series: tuple,
                 words: str) -> None:
    """The 'showSeries' method plots 'series', titled 'title', their
    values in 'unit'; or says 'words' if there are none."""
    self.__curve_title__ = title
    self.__curve_unit__ = unit
    self.__curve_series__ = (*series,)
    self.__curve_words__ = words
    self.update()

  def plotRect(self, ) -> QRectF:
    """The 'plotRect' method returns where the axes are."""
    left, top, right, bottom = self.__fallback_plot_margins__
    width = max(self.width() - left - right, 1.0)
    height = max(self.height() - top - bottom, 1.0)
    return QRectF(left, top, width, height)

  def timeScale(self, ) -> tuple[float, str]:
    """The 'timeScale' method returns what the time is shown in: times a
    thousand in milliseconds for a window shorter than a second, else in
    seconds."""
    return (1000.0, 'ms') if self.window < 1.0 else (1.0, 's')

  def timeAxis(self, ) -> tuple[float, float, float]:
    """The 'timeAxis' method returns where the time axis starts and
    ends, the last 'window' seconds, and its step."""
    window = self.window
    latest = max([line[-1][0] for _, _, line in self.series if line]
                 + [0.0])
    step = niceAbove(window / 5)
    start = max(0.0, step * math.ceil((latest - window) / step - 1e-9))
    return start, start + window, step

  def valueAxis(self, ) -> tuple[float, float, float]:
    """The 'valueAxis' method returns the value axis's ends and step,
    round numbers past the values shown, either side of nought."""
    start, _, _ = self.timeAxis()
    values = [v for _, _, line in self.series for t, v in line
              if t >= start]
    least = self.__fallback_least_value__
    if not values:
      return niceSpan(-least, least, least)
    low, high = min(values), max(values)
    room = 0.08 * max(high - low, 1e-9)
    return niceSpan(low - room, high + room, 1e-9)

  def toScreen(self, time: float, value: float) -> QPointF:
    """The 'toScreen' method returns the pixel a time in seconds and a
    value are plotted at."""
    box = self.plotRect()
    start, end, _ = self.timeAxis()
    bottom, top, _ = self.valueAxis()
    return QPointF(
      box.left() + (time - start) / (end - start) * box.width(),
      box.bottom() - (value - bottom) / (top - bottom) * box.height())

  def lines(self, ) -> list[tuple[str, Color, list[QPointF]]]:
    """The 'lines' method returns the series as pixels, those in the
    time shown."""
    start, _, _ = self.timeAxis()
    return [(name, color, [self.toScreen(t, v) for t, v in line
                           if t >= start])
            for name, color, line in self.series]
