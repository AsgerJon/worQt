"""
PaintLabCurve subclasses 'AbstractPaintOp' and paints the curves of a
'LabCurve' with their axes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QPolygonF

from ....paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from ._lab_curve import LabCurve

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_TICK = 5.0  # pixels: how long a tick is


def _label(value: float) -> str:
  """A tick's number, as short as it reads."""
  return '%g' % round(value, 6)


class PaintLabCurve(AbstractPaintOp):
  """
  PaintLabCurve subclasses 'AbstractPaintOp' and paints a 'LabCurve':
  the title, the peak and the legend above; the axes through nought
  with their gridlines, ticks and names; the curves; the events on the
  actuator's curve and the peak's mark.
  """

  #  Annotations
  widget: LabCurve

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the background in 'rect', then the
    heading, the axes, the curves and their marks."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    series = widget.series()
    self._paintHeading(painter, series)
    self._paintAxes(painter)
    for _, color, points in reversed(series):
      if len(points) > 1:
        painter.setPen(QPen(color.Q, 1.8))
        painter.drawPolyline(QPolygonF(points))
    painter.setPen(QPen(widget.textColor.Q, 1.5))
    painter.setBrush(widget.paddingsColor.fillBrush)
    for _, point in widget.eventPoints():
      painter.drawEllipse(point, 3.5, 3.5)
    peak = widget.peakPoint()
    if peak is not None:
      painter.setPen(QPen(widget.peakColor.Q, 2.0))
      painter.setBrush(widget.peakColor.fillBrush)
      painter.drawEllipse(peak, 4.0, 4.0)
    painter.setBrush(self.emptyBrush)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintHeading(self, painter: WPainter, series: list) -> None:
    """The title and the peak, then the legend, each curve named in its
    colour."""
    widget = self.widget
    box = widget.plotRect()
    painter.setFont(widget.titleFont)
    painter.setPen(widget.titleFont.color.Q)
    title = QRectF(box.left(), 6.0, box.width() / 2, 20.0)
    painter.drawText(title, _LEFT, 'Total force against displacement')
    painter.setFont(widget.font)
    painter.setPen(widget.peakColor.Q)
    peak = QRectF(box.center().x(), 6.0, box.width() / 2, 20.0)
    painter.drawText(peak, _LEFT, widget.peakText())
    left = box.left()
    metrics = widget.font.metrics
    for name, color, _ in series:
      painter.setPen(QPen(color.Q, 2.0))
      painter.drawLine(QLineF(left, 36.0, left + 16.0, 36.0))
      painter.setPen(widget.textColor.Q)
      width = metrics.horizontalAdvance(name) + 4.0
      painter.drawText(QRectF(left + 20.0, 28.0, width, 16.0), _LEFT, name)
      left += width + 36.0
    painter.setPen(widget.peakColor.Q)
    events = QRectF(box.left(), 46.0, box.width(), 16.0)
    painter.drawText(events, _LEFT, widget.eventsText())

  def _paintAxes(self, painter: WPainter) -> None:
    """The gridlines and ticks, the axes through nought, and their
    names."""
    widget = self.widget
    box = widget.plotRect()
    (left, right, across), (bottom, top, up) = widget.axes()
    painter.setFont(widget.font)
    grid = QPen(widget.gridColor.Q, 1.0)
    axis = QPen(widget.axisColor.Q, 1.0)
    for index in range(int(round((right - left) / across)) + 1):
      value = left + index * across
      x = widget.toScreen(value, bottom).x()
      painter.setPen(grid)
      painter.drawLine(QLineF(x, box.top(), x, box.bottom()))
      painter.setPen(axis)
      painter.drawLine(QLineF(x, box.bottom(), x, box.bottom() + _TICK))
      label = QRectF(x - 30.0, box.bottom() + _TICK, 60.0, 16.0)
      painter.drawText(label, _CENTER, _label(value))
    for index in range(int(round((top - bottom) / up)) + 1):
      value = bottom + index * up
      y = widget.toScreen(left, value).y()
      painter.setPen(grid)
      painter.drawLine(QLineF(box.left(), y, box.right(), y))
      painter.setPen(axis)
      painter.drawLine(QLineF(box.left() - _TICK, y, box.left(), y))
      label = QRectF(box.left() - 60.0, y - 8.0, 60.0 - 2 * _TICK, 16.0)
      painter.drawText(label, _RIGHT, _label(value))
    nought = widget.toScreen(0.0, 0.0)
    painter.setPen(axis)
    painter.drawLine(
      QLineF(
        box.left(), nought.y(), box.right(),
        nought.y()
        )
      )
    painter.drawLine(
      QLineF(
        nought.x(), box.top(), nought.x(),
        box.bottom()
        )
      )
    painter.setPen(widget.textColor.Q)
    under = QRectF(box.left(), box.bottom() + 22.0, box.width(), 16.0)
    painter.drawText(under, _CENTER, 'displacement mm, up positive')
    painter.drawText(
      QRectF(4.0, box.top() - 24.0, 56.0, 14.0), _LEFT,
      'force kN'
      )
