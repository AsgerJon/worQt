"""
PaintTabBar subclasses 'AbstractPaintOp' and paints the tabs of a
'TabBar'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QRectF, QPointF

from ..paint_ops import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from PySide6.QtGui import QPaintEvent

  from ..utils import WPainter
  from ..utils.geom import Rect
  from . import TabBar

_CENTER = Qt.AlignmentFlag.AlignCenter
_ELIDE = Qt.TextElideMode.ElideRight


class PaintTabBar(AbstractPaintOp):
  """
  PaintTabBar subclasses 'AbstractPaintOp' and paints the tabs of a
  'TabBar' side by side: each its title, a dot when it holds unsaved
  changes and a cross to close it, the current tab in the colour of the
  page below it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: TabBar

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the bar's background and every tab in
    'rect'.
    """
    bar = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, bar.paddingsColor.fillBrush)
    painter.setClipRect(rect.Q)
    for index in range(bar.count):
      self._paintTab(painter, bar.tabRect(index), index)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintTab(self, painter: WPainter, box: QRectF, index: int) -> None:
    """One tab: its face, its title, and the dot or the cross."""
    bar = self.widget
    current = True if index == bar.currentIndex else False
    face = bar.currentColor if current else bar.tabColor
    painter.setPen(self.emptyPen)
    painter.fillRect(box.adjusted(0, 0, -1, 0), face.fillBrush)
    if current:
      line = QRectF(box.left(), box.top(), box.width() - 1, 2)
      painter.fillRect(line, bar.accentColor.fillBrush)
    closeBox = bar.closeRect(box)
    textBox = QRectF(box.left(), box.top(), closeBox.left() - box.left(),
                     box.height()).adjusted(bar.tabPadding, 0, 0, 0)
    color = bar.currentTextColor if current else bar.textColor
    painter.setFont(bar.font)
    painter.setPen(color.Q)
    title = bar.font.metrics.elidedText(bar.titleAt(index), _ELIDE,
                                        int(max(textBox.width(), 0)))
    painter.drawText(textBox, _CENTER, title)
    if bar.isModified(index):
      self._paintDot(painter, closeBox, color)
    else:
      self._paintCross(painter, closeBox, color)

  def _paintDot(self, painter: WPainter, box: QRectF, color) -> None:
    radius = box.width() * 0.2
    painter.setPen(self.emptyPen)
    painter.setBrush(color.fillBrush)
    painter.drawEllipse(box.center(), radius, radius)

  def _paintCross(self, painter: WPainter, box: QRectF, color) -> None:
    half = box.width() * 0.18
    center = box.center()
    painter.setPen(color.solidPen)
    painter.drawLine(center + QPointF(-half, -half),
                     center + QPointF(half, half))
    painter.drawLine(center + QPointF(-half, half),
                     center + QPointF(half, -half))
