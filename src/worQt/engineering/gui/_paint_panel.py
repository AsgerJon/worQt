"""
The paint operations of the window's panels: 'PaintPanel' paints a
plain panel, 'PaintInspector' the 'DiskInspector's title and row names.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF

from ...paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter
  from ...utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class PaintPanel(AbstractPaintOp):
  """
  PaintPanel subclasses 'AbstractPaintOp' and paints a plain panel: its
  colour, and a divider along the side facing the drawing.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method fills 'rect' and draws the divider."""
    widget, box = self.widget, QRectF(rect.Q)
    painter.fillRect(box, widget.panelColor.fillBrush)
    painter.setPen(widget.dividerColor.solidPen)
    first, last = widget.dividerLine()
    painter.drawLine(first, last)
    return rect


class PaintInspector(AbstractPaintOp):
  """
  PaintInspector subclasses 'AbstractPaintOp' and paints the
  'DiskInspector's title, the edge under it, the name of each row beside
  its field and the note below the rows.
  """

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the words of the panel."""
    widget = self.widget
    painter.setFont(widget.titleFont)
    painter.setPen(widget.titleColor.Q)
    painter.drawText(widget.titleRect(), _LEFT, widget.title)
    painter.setFont(widget.font)
    painter.setPen(widget.wordColor.Q)
    painter.drawText(widget.subtitleRect(), _LEFT, widget.subtitle)
    for name, field in zip(widget.rowNames, widget.fields):
      box = QRectF(
        widget.margin, field.y(), widget.labelWidth,
        field.height()
        )
      painter.drawText(box, _LEFT, name)
    painter.drawText(widget.noteRect(), _LEFT, widget.note)
    return rect
