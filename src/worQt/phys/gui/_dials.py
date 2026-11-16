"""
The speedometer's dial (user, 2026-11-15: "let's add a speedometer.
both a virtual one on the GUI and a diegetic one next to the steering
wheel"), painted once: a period instrument's black face, its scale in
white every 10 km/h (longer every 20, a figure every 40) round the
needle's sweep ('_gauge.SWEEP', 'TOP_SPEED'), 'km/h' under the middle.
The car's dial on its dash wears it ('_gauge.faceRows'), the window's
speedometer shows it under its needle ('phys.qml').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import tempfile
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter, QPen

from .._gauge import TOP_SPEED, angleOf

#  The picture's side, px; its face's colour, its scale's, the ring's
#  round the face; the picture's form (one painted to another form is
#  painted anew).
SIZE = 512
FACE_TONE, MARK_TONE, RING_TONE = (QColor(16, 16, 18),
                                   QColor(236, 236, 230),
                                   QColor(120, 122, 126))
DIAL_FORM = 1


def dialFile() -> str:
  """The 'dialFile' function returns the dial's picture, painted to the
  temp folder once ('dialPicture')."""
  path = Path(tempfile.gettempdir()) / ('worqt-phys-dial-%d.png' % (
    DIAL_FORM))
  if not path.exists():
    dialPicture(str(path))
  return str(path)


def dialPicture(path: str) -> None:
  """The 'dialPicture' function paints the speedometer's dial and saves
  it at 'path' (a PNG, square, the dial round within): the face, a thin
  ring round it, the scale's marks from the middle out (at 'angleOf' of
  each speed: right of upright as seen), its figures, 'km/h'."""
  image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
  image.fill(QColor(0, 0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  middle, radius = QPointF(0.5 * SIZE, 0.5 * SIZE), 0.5 * SIZE
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(RING_TONE))
  painter.drawEllipse(middle, radius, radius)
  painter.setBrush(QBrush(FACE_TONE))
  painter.drawEllipse(middle, 0.97 * radius, 0.97 * radius)
  for speed in range(0, int(TOP_SPEED) + 1, 10):
    angle = angleOf(float(speed))
    way = QPointF(math.sin(angle), -math.cos(angle))
    major = speed % 20 == 0
    inner = (0.76 if major else 0.83) * radius
    painter.setPen(QPen(MARK_TONE, 0.022 * radius if major else
                        0.012 * radius, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.FlatCap))
    painter.drawLine(middle + way * inner, middle + way * (0.92 * radius))
    if speed % 40 == 0:
      painter.setFont(_fontOf(0.13 * radius))
      box = QRectF(0.0, 0.0, 0.4 * radius, 0.2 * radius)
      box.moveCenter(middle + way * (0.58 * radius))
      painter.drawText(box, Qt.AlignmentFlag.AlignCenter, str(speed))
  painter.setPen(QPen(MARK_TONE.darker(130)))
  painter.setFont(_fontOf(0.09 * radius))
  box = QRectF(0.0, 0.0, 0.6 * radius, 0.15 * radius)
  box.moveCenter(middle + QPointF(0.0, 0.42 * radius))
  painter.drawText(box, Qt.AlignmentFlag.AlignCenter, 'km/h')
  painter.end()
  image.save(path)


def _fontOf(pixels: float) -> QFont:
  """Returns a plain sans font 'pixels' px tall."""
  font = QFont('Sans Serif')
  font.setPixelSize(max(1, round(pixels)))
  font.setBold(True)
  return font
