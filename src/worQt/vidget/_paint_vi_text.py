"""
PaintViText subclasses 'AbstractPaintOp' and paints the text of a
'Vidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPointF

from ..paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QPaintEvent

  from ..utils import WPainter
  from ..utils.geom import Rect
  from . import VidgetBase


class PaintViText(AbstractPaintOp):
  """
  PaintViText subclasses 'AbstractPaintOp' and paints the text of a
  'Vidget' in the area it is given: the paper, the shown text laid out
  across it, and the cursor while the vidget shows one - a block on the
  character in 'NORMAL' mode, a thin bar between characters in
  'INSERT'.
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
    The 'paint' method fills 'rect' with the paper colour, draws the
    shown text laid out to the width of 'rect' and scrolled, and the
    cursor over it.
    """
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, self.widget.paddingsColor.fillBrush)
    painter.setFont(self.widget.font)
    painter.setClipRect(rect.Q)
    layout = self.widget.viewLayout(rect.width, rect.height)
    offset = self.widget.scrollOffset(layout)
    origin = QPointF(rect.left, rect.top - offset)
    layout.draw(painter, origin)
    if self.widget.showsCursor():
      cursorRect = self.widget.cursorRect(layout).translated(origin)
      painter.fillRect(cursorRect, self.widget.cursorColor.fillBrush)
    return rect
