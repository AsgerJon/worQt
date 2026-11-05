"""
PaintLineNumbers subclasses 'AbstractPaintOp' and paints the line
numbers of a 'Vidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF

from ..paint_ops import AbstractPaintOp
from ..utils.geom import Rect

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QPaintEvent

  from ..utils import WPainter
  from . import VidgetBase

_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter


class PaintLineNumbers(AbstractPaintOp):
  """
  PaintLineNumbers subclasses 'AbstractPaintOp' and claims a gutter along
  the left of the area it is given for the line numbers of a 'Vidget',
  always shown, as Vi's 'number' option shows them: each line's number
  beside the first row it is laid out on, the rows a long line wraps
  onto left unnumbered, and the cursor's line in a stronger colour. It
  hands the rest of the area on, for the text.
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
    The 'paint' method paints the numbers of the lines in view down the
    gutter, scrolled as the text is, and returns the area right of it.
    """
    vidget, width = self.widget, min(self.widget.gutterWidth, rect.width)
    gutter = Rect(rect.left, rect.top, rect.left + width, rect.bottom)
    textRect = Rect(rect.left + width, rect.top, rect.right, rect.bottom)
    painter.setPen(self.emptyPen)
    painter.fillRect(gutter.Q, vidget.gutterColor.fillBrush)
    painter.setFont(vidget.font)
    painter.setClipRect(gutter.Q)
    layout = vidget.viewLayout(textRect.width, textRect.height)
    offset = vidget.scrollOffset(layout)
    cursorLine = vidget.lineNumberAt(vidget.cursor)
    numberWidth = width - vidget.gutterInset
    for row in range(vidget.scrollTop, layout.lineCount()):
      line = layout.lineAt(row)
      top = rect.top + line.y() - offset
      if top > rect.bottom:
        break
      start = line.textStart()
      if start and vidget.text[start - 1] != '\n':
        continue  # a row a long line wrapped onto
      number = vidget.lineNumberAt(start)
      current = True if number == cursorLine else False
      color = vidget.currentNumberColor if current else vidget.numberColor
      painter.setPen(color.Q)
      box = QRectF(gutter.left, top, numberWidth, line.height())
      painter.drawText(box, _RIGHT, str(number + 1))
    return textRect
