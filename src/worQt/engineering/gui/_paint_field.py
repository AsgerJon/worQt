"""
The paint operations of the panel's controls: 'PaintFieldBox' paints the
rounded box of a 'NumberField' or a 'ToolButton', 'PaintButtonText' a
button's text and 'PaintFieldNumber' a field's number and unit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter

from ...paint_ops import AbstractPaintOp
from ...utils.geom import Rect

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter

_CENTER = Qt.AlignmentFlag.AlignCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class PaintFieldBox(AbstractPaintOp):
  """
  PaintFieldBox subclasses 'AbstractPaintOp' and paints the rounded box
  of a 'NumberField' or a 'ToolButton' in the face and frame colours its
  state calls for, handing on the room inside the box.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the box, and returns the room inside."""
    widget = self.widget
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = QRectF(rect.Q).adjusted(1.0, 1.0, -1.0, -1.0)
    painter.setPen(widget.frameColor.solidPen)
    painter.setBrush(widget.faceColor.fillBrush)
    painter.drawRoundedRect(box, 4.0, 4.0)
    return Rect(box.adjusted(8.0, 0.0, -8.0, 0.0))


class PaintButtonText(AbstractPaintOp):
  """
  PaintButtonText subclasses 'AbstractPaintOp' and paints a
  'ToolButton's text, centred.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the text centred in 'rect'."""
    widget = self.widget
    painter.setFont(widget.font)
    painter.setPen(widget.inkColor.Q)
    painter.drawText(rect.Q, _CENTER, widget.text)
    return rect


class PaintFieldNumber(AbstractPaintOp):
  """
  PaintFieldNumber subclasses 'AbstractPaintOp' and paints a
  'NumberField's number, right aligned before its unit, with a caret
  after it while it is typed in, and marked while the next key replaces
  it.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the number and the unit in 'rect'."""
    widget, inner = self.widget, QRectF(rect.Q)
    metrics = widget.font.metrics
    painter.setFont(widget.font)
    unitWidth = metrics.horizontalAdvance(widget.unit) + 6.0
    numberBox = inner.adjusted(0.0, 0.0, -unitWidth, 0.0)
    text, editing = widget.shownText, widget.editText is not None
    textWidth = metrics.horizontalAdvance(text)
    if editing and widget.replaceNext and text:
      mark = QRectF(
        numberBox.right() - textWidth - 2.0, inner.top() + 5.0,
        textWidth + 4.0, inner.height() - 10.0
        )
      painter.fillRect(mark, widget.markColor.fillBrush)
    painter.setPen(widget.inkColor.Q)
    painter.drawText(numberBox, _RIGHT, text)
    if editing and not widget.replaceNext:
      x = numberBox.right() + 1.5
      painter.drawLine(
        QPointF(x, inner.top() + 6.0),
        QPointF(x, inner.bottom() - 6.0)
        )
    painter.setPen(widget.unitColor.Q)
    painter.drawText(inner, _RIGHT, widget.unit)
    return rect
