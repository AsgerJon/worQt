"""
PaintSlider subclasses 'AbstractPaintOp' and paints a 'Slider'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter

from ...paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ...utils import WPainter
  from ...utils.geom import Rect
  from . import Slider

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class PaintSlider(AbstractPaintOp):
  """
  PaintSlider subclasses 'AbstractPaintOp' and paints a 'Slider': its
  name, the track, filled in the accent colour up to the handle, the
  handle, lighter under the mouse, and the share it is at.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: Slider

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the background, the name, the track,
    the handle and the share."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setFont(widget.font)
    painter.setPen(widget.inkColor.Q)
    painter.drawText(widget.textRect(), _LEFT, widget.text)
    painter.drawText(widget.valueRect(), _RIGHT, widget.valueText())
    track = widget.trackRect()
    corner = track.height() / 2
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.trackColor.fillBrush)
    painter.drawRoundedRect(track, corner, corner)
    center = widget.handleCenter()
    filled = QRectF(
      track.left(), track.top(),
      center.x() - track.left(), track.height()
      )
    painter.setBrush(widget.fillColor.fillBrush)
    painter.drawRoundedRect(filled, corner, corner)
    radius = widget.handleRadius()
    painter.setBrush(widget.handleColor.fillBrush)
    painter.drawEllipse(center, radius, radius)
    painter.setBrush(self.emptyBrush)
    return rect
