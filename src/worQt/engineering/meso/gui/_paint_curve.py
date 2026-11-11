"""
PaintCurve subclasses 'AbstractPaintOp' and paints the stress-strain
curve of a 'CurveWidget' with its axes.
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
  from . import CurveWidget

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_CENTER = Qt.AlignmentFlag.AlignCenter
_TICK = 5.0  # pixels: how long a tick is


def _label(value: float) -> str:
  """A tick's number, as short as it reads."""
  return '%g' % round(value, 6)


class PaintCurve(AbstractPaintOp):
  """
  PaintCurve subclasses 'AbstractPaintOp' and paints the stress-strain
  curve of a 'CurveWidget': the test's name, the strength and the
  stiffness read off it, above; the axes with their gridlines, ticks and
  names; the curve; and a mark where the strength was reached.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: CurveWidget

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the background in 'rect', then the
    heading, the axes, the curve and the strength's mark.
    """
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    self._paintHeading(painter)
    self._paintAxes(painter)
    points = widget.curvePoints()
    if len(points) > 1:
      painter.setPen(QPen(widget.curveColor.Q, 2.0))
      painter.drawPolyline(QPolygonF(points))
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

  def _paintHeading(self, painter: WPainter) -> None:
    """The test's name, then the strength and the stiffness."""
    widget = self.widget
    box = widget.plotRect()
    painter.setFont(widget.titleFont)
    painter.setPen(widget.titleFont.color.Q)
    title = QRectF(box.left(), 8.0, box.width(), 22.0)
    painter.drawText(title, _LEFT, widget.title())
    painter.setFont(widget.font)
    painter.setPen(widget.peakColor.Q)
    peak = QRectF(box.left(), 30.0, box.width() / 2, 18.0)
    painter.drawText(peak, _LEFT, widget.peakText())
    painter.setPen(widget.textColor.Q)
    stiffness = QRectF(box.center().x(), 30.0, box.width() / 2, 18.0)
    painter.drawText(stiffness, _LEFT, widget.stiffnessText())

  def _paintAxes(self, painter: WPainter) -> None:
    """The gridlines and ticks, the axes and their names."""
    widget = self.widget
    box = widget.plotRect()
    strainEnd, stressEnd = widget.axisEnds()
    strainStep, stressStep = widget.axisSteps()
    painter.setFont(widget.font)
    grid = QPen(widget.gridColor.Q, 1.0)
    axis = QPen(widget.axisColor.Q, 1.0)
    count = int(strainEnd / strainStep + 1e-9)
    for index in range(count + 1):
      x = widget.toScreen(index * strainStep, 0.0).x()
      painter.setPen(grid)
      painter.drawLine(QLineF(x, box.top(), x, box.bottom()))
      painter.setPen(axis)
      painter.drawLine(QLineF(x, box.bottom(), x, box.bottom() + _TICK))
      label = QRectF(x - 30.0, box.bottom() + _TICK, 60.0, 18.0)
      painter.drawText(label, _CENTER, _label(index * strainStep))
    count = int(stressEnd / stressStep + 1e-9)
    for index in range(count + 1):
      y = widget.toScreen(0.0, index * stressStep).y()
      painter.setPen(grid)
      painter.drawLine(QLineF(box.left(), y, box.right(), y))
      painter.setPen(axis)
      painter.drawLine(QLineF(box.left() - _TICK, y, box.left(), y))
      label = QRectF(box.left() - 60.0, y - 9.0, 60.0 - 2 * _TICK, 18.0)
      painter.drawText(label, _RIGHT, _label(index * stressStep))
    painter.setPen(axis)
    corner = QPointF(box.left(), box.bottom())
    painter.drawLine(QLineF(corner, QPointF(box.right(), box.bottom())))
    painter.drawLine(QLineF(corner, QPointF(box.left(), box.top())))
    painter.setPen(widget.textColor.Q)
    under = QRectF(box.left(), box.bottom() + 24.0, box.width(), 18.0)
    painter.drawText(under, _CENTER, 'strain ‰')
    above = QRectF(box.left() - 56.0, box.top() - 22.0, 120.0, 18.0)
    painter.drawText(above, _LEFT, 'stress MPa')
