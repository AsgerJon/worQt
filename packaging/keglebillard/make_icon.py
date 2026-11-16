"""
Draws Keglebillard's icon, 'icon.png' beside this script (1024 x 1024):
on kegler's cyan cloth a pin, its outline the game's own
('KeglePin().profile', its three dark grooves), and the red ball by it.
Run from the repo's root with 'src' on the path; PyInstaller makes the
Mac's icon from the picture.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QGuiApplication, QImage
from PySide6.QtGui import QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtGui import QRadialGradient

from worQt.gaming.billiards import KeglePin

SIZE = 1024
HERE = Path(__file__).resolve().parent


def drawn() -> QImage:
  """Returns the icon drawn."""
  image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
  image.fill(Qt.GlobalColor.transparent)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  cloth = QRadialGradient(QPointF(0.45 * SIZE, 0.35 * SIZE), 0.8 * SIZE)
  cloth.setColorAt(0.0, QColor('#2fd0dc'))
  cloth.setColorAt(1.0, QColor('#0b7f8a'))
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(cloth))
  painter.drawRoundedRect(QRectF(40, 40, SIZE - 80, SIZE - 80), 180, 180)
  pin = KeglePin()
  scale = 0.62 * SIZE / 120.0
  foot = QPointF(0.44 * SIZE, 0.84 * SIZE)
  left, right = [], []
  for y, r in pin.profile:
    left.append(QPointF(foot.x() - r * scale, foot.y() - y * scale))
    right.append(QPointF(foot.x() + r * scale, foot.y() - y * scale))
  outline = QPainterPath(left[0])
  for point in left[1:] + right[::-1]:
    outline.lineTo(point)
  outline.closeSubpath()
  wood = QLinearGradient(foot.x() - 12 * scale, 0, foot.x() + 12 * scale, 0)
  wood.setColorAt(0.0, QColor('#f3e1bd'))
  wood.setColorAt(0.6, QColor('#dcbf92'))
  wood.setColorAt(1.0, QColor('#9c7a4c'))
  painter.setBrush(QBrush(wood))
  painter.setPen(QPen(QColor(60, 40, 20, 160), 6))
  painter.drawPath(outline)
  painter.setPen(QPen(QColor('#5a3a20'), 9, Qt.PenStyle.SolidLine,
                      Qt.PenCapStyle.RoundCap))
  for y in (64.0, 66.5, 69.0):
    r = pin.radiusAt(y) * scale
    painter.drawLine(QPointF(foot.x() - r, foot.y() - y * scale),
                     QPointF(foot.x() + r, foot.y() - y * scale))
  ball = QRadialGradient(QPointF(0.70 * SIZE, 0.69 * SIZE), 0.13 * SIZE)
  ball.setColorAt(0.0, QColor('#ff8a80'))
  ball.setColorAt(0.35, QColor('#d0202a'))
  ball.setColorAt(1.0, QColor('#5c0a0e'))
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QColor(0, 0, 0, 70))
  painter.drawEllipse(QRectF(0.62 * SIZE, 0.83 * SIZE, 0.22 * SIZE,
                             0.05 * SIZE))
  painter.setBrush(QBrush(ball))
  painter.drawEllipse(QPointF(0.73 * SIZE, 0.74 * SIZE), 0.11 * SIZE,
                      0.11 * SIZE)
  painter.end()
  return image


if __name__ == '__main__':
  app = QGuiApplication(sys.argv)
  target = HERE / 'icon.png'
  if not drawn().save(str(target)):
    raise OSError('the icon could not be saved to %s' % target)
  print('icon drawn to', target)
