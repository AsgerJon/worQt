"""
PaintCheckBox subclasses 'AbstractPaintOp' and paints a 'CheckBox'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QPen, QPolygonF

from ...paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter
  from ...utils.geom import Rect
  from . import CheckBox

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class PaintCheckBox(AbstractPaintOp):
  """
  PaintCheckBox subclasses 'AbstractPaintOp' and paints a 'CheckBox': the
  box, lighter under the mouse, a tick in it in the accent colour when
  ticked, and its text beside it, dimmed when greyed out.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: CheckBox

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the background, the box, its tick and
    its text."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    box = widget.boxRect()
    painter.setBrush(self.emptyBrush)
    painter.setPen(QPen(widget.frameColor.Q, 1.5))
    painter.drawRoundedRect(box, 2.0, 2.0)
    if widget.checked:
      left, top = box.left(), box.top()
      size = box.width()
      tick = QPolygonF(
          [
            QPointF(left + 0.2 * size, top + 0.52 * size),
            QPointF(left + 0.42 * size, top + 0.74 * size),
            QPointF(left + 0.8 * size, top + 0.28 * size),
          ]
      )
      painter.setPen(QPen(widget.tickColor.Q, 2.2))
      painter.drawPolyline(tick)
    painter.setFont(widget.font)
    painter.setPen(widget.inkColor.Q)
    painter.drawText(widget.textRect(), _LEFT, widget.text)
    return rect
