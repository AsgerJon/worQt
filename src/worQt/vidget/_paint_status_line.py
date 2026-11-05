"""
PaintStatusLine subclasses 'AbstractPaintOp' and paints the status line
of a 'Vidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt

from ..paint_ops import AbstractPaintOp
from ..utils.geom import Rect

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QPaintEvent

  from ..utils import WPainter
  from . import VidgetBase

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_TEXT_INSET = 4  # pixels between the status text and the strip's ends


class PaintStatusLine(AbstractPaintOp):
  """
  PaintStatusLine subclasses 'AbstractPaintOp' and claims the bottom row
  of the content area for the status line of a 'Vidget': its
  'statusLeft' on the left, such as '-- INSERT --' or the ex command
  being written, and its 'statusRight' on the right, the cursor's line
  and column. It hands the rest of the area on, for the text.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: VidgetBase

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the status line along the bottom of 'rect'
    and returns what is left of 'rect' above it.
    """
    height = min(self.widget.statusHeight, rect.height)
    top = rect.bottom - height
    strip = Rect(rect.left, top, rect.right, rect.bottom)
    painter.setPen(self.emptyPen)
    painter.fillRect(strip.Q, self.widget.statusColor.fillBrush)
    painter.setFont(self.widget.font)
    textRect = strip.Q.adjusted(_TEXT_INSET, 0, -_TEXT_INSET, 0)
    painter.drawText(textRect, _LEFT, self.widget.statusLeft)
    painter.drawText(textRect, _RIGHT, self.widget.statusRight)
    return Rect(rect.left, rect.top, rect.right, top)
