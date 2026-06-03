"""
Small painter-built icons for the drawing app's tool palette, so no image
asset files are needed. Each function returns a 24x24 'QIcon': a four-way
arrow for navigate, a pointer for select, a crossed node for anchor points,
a bold full-width line for module lines, and the dimension glyphs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (
  QIcon,
  QPixmap,
  QPainter,
  QPen,
  QColor,
  QBrush,
  QPolygonF,
)

if TYPE_CHECKING:  # pragma: no cover
  pass


def _canvas() -> tuple:
  """A blank 24x24 transparent pixmap and an antialiased painter on it."""
  pixmap = QPixmap(24, 24)
  pixmap.fill(Qt.GlobalColor.transparent)
  painter = QPainter(pixmap)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  return pixmap, painter


def _triangle(*points: tuple) -> QPolygonF:
  """A 'QPolygonF' from '(x, y)' integer points."""
  return QPolygonF([QPointF(x, y) for x, y in points])


def navigateIcon() -> QIcon:
  """A four-way move arrow for the navigate (pan) tool."""
  pixmap, painter = _canvas()
  colour = QColor('#abb2bf')
  painter.setPen(QPen(colour, 2))
  painter.drawLine(12, 5, 12, 19)
  painter.drawLine(5, 12, 19, 12)
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(colour))
  painter.drawPolygon(_triangle((12, 3), (8, 7), (16, 7)))
  painter.drawPolygon(_triangle((12, 21), (8, 17), (16, 17)))
  painter.drawPolygon(_triangle((3, 12), (7, 8), (7, 16)))
  painter.drawPolygon(_triangle((21, 12), (17, 8), (17, 16)))
  painter.end()
  return QIcon(pixmap)


def anchorIcon() -> QIcon:
  """A small circle with a cross for the anchor-point tool (a node glyph)."""
  pixmap, painter = _canvas()
  painter.setPen(QPen(QColor('#c678dd'), 2))
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.drawEllipse(QPointF(12, 12), 4, 4)
  painter.drawLine(12, 4, 12, 20)
  painter.drawLine(4, 12, 20, 12)
  painter.end()
  return QIcon(pixmap)


def moduleIcon() -> QIcon:
  """A prominent full-width line with an origin dot for the module tool."""
  pixmap, painter = _canvas()
  colour = QColor('#7fbf63')
  painter.setPen(QPen(colour, 2))
  painter.drawLine(2, 16, 22, 8)  # a bold, edge-to-edge super-gridline
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(colour))
  painter.drawEllipse(QPointF(7, 14), 2.5, 2.5)  # the origin point
  painter.end()
  return QIcon(pixmap)


def memberIcon() -> QIcon:
  """A solid member between two end nodes for the structural-member tool."""
  pixmap, painter = _canvas()
  colour = QColor('#61afef')
  painter.setPen(QPen(colour, 3))
  painter.drawLine(6, 18, 18, 6)  # the member body
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(colour))
  painter.drawEllipse(QPointF(6, 18), 2.5, 2.5)  # end nodes
  painter.drawEllipse(QPointF(18, 6), 2.5, 2.5)
  painter.end()
  return QIcon(pixmap)


def supportIcon() -> QIcon:
  """A pinned-support triangle on hatched ground for the support tool."""
  pixmap, painter = _canvas()
  colour = QColor('#56b6c2')
  painter.setPen(QPen(colour, 2))
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.drawPolygon(_triangle((12, 6), (6, 17), (18, 17)))  # the support
  painter.drawLine(4, 17, 20, 17)  # ground line
  for x in (7, 12, 17):  # hatching
    painter.drawLine(x, 17, x - 3, 21)
  painter.end()
  return QIcon(pixmap)


def loadIcon() -> QIcon:
  """A downward force arrow for the nodal-load tool."""
  pixmap, painter = _canvas()
  colour = QColor('#e06c75')
  painter.setPen(QPen(colour, 2))
  painter.drawLine(12, 4, 12, 18)  # the force shaft
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(colour))
  painter.drawPolygon(_triangle((12, 21), (8, 15), (16, 15)))  # arrowhead
  painter.end()
  return QIcon(pixmap)


def selectIcon() -> QIcon:
  """A pointer-arrow glyph for the select tool."""
  pixmap, painter = _canvas()
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(QColor('#abb2bf')))
  painter.drawPolygon(_triangle(
      (6, 4), (6, 19), (10, 15), (13, 21), (15, 20), (12, 14), (17, 14)))
  painter.end()
  return QIcon(pixmap)


def angleIcon() -> QIcon:
  """Two rays from a vertex with a small arc, for the angle tool."""
  pixmap, painter = _canvas()
  colour = QColor('#ffd24a')
  painter.setPen(QPen(colour, 2))
  painter.drawLine(5, 19, 20, 19)  # horizontal ray
  painter.drawLine(5, 19, 18, 7)  # slanted ray
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.drawArc(QRectF(-1.0, 13.0, 16.0, 16.0), 0, 45 * 16)  # arc at vertex
  painter.end()
  return QIcon(pixmap)


def dimensionIcon() -> QIcon:
  """A dimension line (extension ticks + double arrowheads) for the tool."""
  pixmap, painter = _canvas()
  colour = QColor('#ffd24a')
  painter.setPen(QPen(colour, 2))
  painter.drawLine(5, 6, 5, 18)  # extension lines
  painter.drawLine(19, 6, 19, 18)
  painter.drawLine(5, 12, 19, 12)  # dimension line
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(colour))
  painter.drawPolygon(_triangle((5, 12), (9, 9), (9, 15)))
  painter.drawPolygon(_triangle((19, 12), (15, 9), (15, 15)))
  painter.end()
  return QIcon(pixmap)
