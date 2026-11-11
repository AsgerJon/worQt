"""
PaintSection subclasses 'AbstractPaintOp' and paints the section of a
'SectionWidget': mortar, stones, platens and cracks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen

from ....paint_ops import AbstractPaintOp
from ...gui import crackLevel, levelColor, paintCrackScale
from ...gui import CRACK_LEVELS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from . import SectionWidget

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_ROUNDING = 0.6  # mm: how round a stone's corners are drawn


def roundedPath(points: list[QPointF], radius: float) -> QPainterPath:
  """The 'roundedPath' function returns the polygon through 'points' with
  its corners rounded off, each by up to 'radius' along its edges, never
  more than four tenths of an edge."""
  path = QPainterPath()
  count = len(points)
  for index, corner in enumerate(points):
    before, after = points[index - 1], points[(index + 1) % count]
    into = _towards(corner, before, radius)
    out = _towards(corner, after, radius)
    if index:
      path.lineTo(into)
    else:
      path.moveTo(into)
    path.quadTo(corner, out)
  path.closeSubpath()
  return path


def _towards(start: QPointF, end: QPointF, radius: float) -> QPointF:
  """The point 'radius' from 'start' towards 'end', or four tenths of
  the way if that is nearer."""
  along = end - start
  length = (along.x() ** 2 + along.y() ** 2) ** 0.5
  if length <= 0.0:
    return QPointF(start)
  return start + along * (min(radius, 0.4 * length) / length)


class PaintSection(AbstractPaintOp):
  """
  PaintSection subclasses 'AbstractPaintOp' and paints the section of a
  'SectionWidget' to scale: the mortar, each stone it cuts a polygon on
  it with its corners rounded off, the platens in steel above and
  below, the caption above, and, over it all, the cracks of the test
  shown, each face given drawn as a line coloured by how far, and the
  colour scale below the caption. Paste less than solid shows the
  stones behind the cut through it, as the widget draws them.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: SectionWidget

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """
    The 'paint' method paints the background in 'rect', then the
    section, its stones, its platens, its caption and its cracks.
    """
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    lattice = widget.lattice
    if lattice is None:
      return rect
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    self._paintPaste(painter, widget.sectionRect())
    self._paintStones(painter)
    self._paintPlatens(painter)
    self._paintCracks(painter)
    painter.setFont(widget.font)
    painter.setPen(widget.textColor.Q)
    caption = QRectF(8.0, 4.0, widget.width() - 16.0, 18.0)
    painter.drawText(caption, _LEFT, widget.caption())
    if widget.test is not None:
      paintCrackScale(painter, widget.crackScaleRect(), widget.font)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _paintPaste(self, painter: WPainter, box: QRectF) -> None:
    """The paste: solid, or as clear as it is, showing the stones
    behind the cut when the cylinder is shown."""
    widget = self.widget
    opacity = widget.pasteOpacity
    if opacity >= 1.0:
      painter.fillRect(box, widget.mortarColor.fillBrush)
    elif widget.cylinder is not None:
      painter.drawPixmap(QPointF(0.0, 0.0), widget.seeThrough())
    else:
      paste = QColor(widget.mortarColor.Q)
      paste.setAlphaF(opacity)
      painter.fillRect(box, paste)

  def _paintStones(self, painter: WPainter) -> None:
    """Each stone the section cuts, its corners rounded off, in the
    stone's colour."""
    widget = self.widget
    radius = _ROUNDING * widget.scale()
    painter.setPen(self.emptyPen)
    painter.setBrush(widget.stoneColor.fillBrush)
    for polygon in widget.lattice.stones:
      points = [widget.toScreen(x, y) for x, y in polygon.tolist()]
      painter.drawPath(roundedPath(points, radius))
    painter.setBrush(self.emptyBrush)

  def _paintPlatens(self, painter: WPainter) -> None:
    """The platens in steel, against the bottom and the top."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    for platen in widget.platenRects():
      painter.fillRect(platen, widget.platenColor.fillBrush)

  def _paintCracks(self, painter: WPainter) -> None:
    """The cracks, each coloured by how far it has given, a colour at a
    time."""
    widget = self.widget
    groups = [[] for _ in range(CRACK_LEVELS)]
    for start, end, size in widget.crackSegments():
      groups[crackLevel(size)].append(QLineF(start, end))
    for level, lines in enumerate(groups):
      if lines:
        painter.setPen(QPen(levelColor(level), 1.5))
        painter.drawLines(lines)
