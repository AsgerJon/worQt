"""
PaintCylinder subclasses 'AbstractPaintOp' and paints the cylinder of a
'CylinderView': paste, stones and cracks layer by layer, and platens.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen

from ....paint_ops import AbstractPaintOp
from ...gui import crackLevel, levelColor, paintCrackScale
from ...gui import CRACK_LEVELS

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from . import CylinderView

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter


class PaintCylinder(AbstractPaintOp):
  """
  PaintCylinder subclasses 'AbstractPaintOp' and paints the cylinder of a
  'CylinderView', layer by layer of paste, the deepest first: the stones
  whose centres are in the layer, then the cracks in it, then the
  layer's paste over them; solid, the paste over all of it; and the
  cracks of the nearest layer, the paste's surface, over its paste.
  Then the platens in steel above and below, and the caption.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Annotations
  widget: CylinderView

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the background in 'rect', then the
    cylinder layer by layer, its platens and its caption."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    if not widget.shown():
      return rect
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    layers = widget.pasteLayers()
    pictures = widget.stoneLayers()
    cracks = [[] for _ in layers]
    for polygon, width, layer in widget.crackPolygons():
      cracks[layer].append((polygon, width))
    last = len(layers) - 1
    for index, ((place, alpha), picture) in enumerate(
        zip(
            layers,
            pictures
            )
        ):
      painter.drawPixmap(QPointF(0.0, 0.0), picture)
      if index < last:
        self._paintCracks(painter, cracks[index])
      paste = QColor(widget.mortarColor.Q)
      paste.setAlphaF(alpha)
      painter.fillRect(place, paste)
    if widget.pasteOpacity >= 1.0:
      painter.fillRect(widget.viewRect(), widget.mortarColor.fillBrush)
    self._paintCracks(painter, cracks[last])
    painter.setPen(self.emptyPen)
    for platen in widget.platenRects():
      painter.fillRect(platen, widget.platenColor.fillBrush)
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

  def _paintCracks(self, painter: WPainter, cracks: list) -> None:
    """The cracks of a layer, each coloured by how far it has given,
    grouped by colour."""
    if not cracks:
      return
    groups = [[] for _ in range(CRACK_LEVELS)]
    for polygon, size in cracks:
      groups[crackLevel(size)].append(polygon)
    for level, polygons in enumerate(groups):
      if not polygons:
        continue
      color = levelColor(level)
      painter.setPen(QPen(color, 0.8))
      painter.setBrush(color)
      for polygon in polygons:
        painter.drawPolygon(polygon)
    painter.setBrush(self.emptyBrush)
