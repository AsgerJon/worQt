"""
The cabin's pictures, painted once (Qt's painter) and kept in the looks'
cache (user, 2026-11-16: "Have the rest of it have the contents of a
camping cabin. Not a fire place, but the same ... 'hygge'"): the walls'
pine planks, the floor's oak boards, a braided rag rug, a knitted
blanket; and the warp knob's enchantment glint ("give it a sort of
enchantment glint, as it is kinda... magic") and the gravity knob's,
more of it (2026-11-17: "And has lots o glint"). Each tiles: its right
edge meets its left, its top its foot.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
import random

from ._looks import cacheFolder

#  The pictures' version (a change paints them anew) and sizes, pixels.
VERSION = 5
SIZE = 512
#  How many m one picture of each covers (its tile).
PINE_TILE = 1.2
BOARD_TILE = 1.6


def cabinPicturesReady() -> dict:
  """Returns the cabin's pictures' files by name ('pine', 'boards',
  'rug', 'blanket', 'glint', 'sparkle'), painted if not kept yet."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  out = {}
  for name, painter in (('pine', pinePainted), ('boards', boardsPainted),
                        ('rug', rugPainted), ('blanket', blanketPainted),
                        ('glint', glintPainted),
                        ('sparkle', sparklePainted)):
    target = folder / ('cabin-%s-%d.png' % (name, VERSION))
    if not target.exists() and not painter().save(str(target)):
      raise OSError('the picture %s could not be kept in %s' % (name,
                                                               target))
    out[name] = target
  return out


def _planks(count: int, light: tuple, seed: int, staggered: bool) -> object:
  """Returns 'count' planks across a tile, wood of about 'light' (red,
  green, blue), each its own shade, grain along it, the seams dark; their
  ends staggered ('staggered': floorboards) or running through."""
  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(SIZE, SIZE, QImage.Format.Format_RGB32)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  wood = random.Random(seed)
  high = SIZE / count
  for k in range(count):
    y = k * high
    shade = wood.uniform(-18, 18)
    colour = QColor(*(max(0, min(255, int(c + shade))) for c in light))
    painter.fillRect(QRectF(0, y, SIZE, high), colour)
    for _ in range(26):
      at = y + wood.uniform(2, high - 2)
      wave, phase = wood.uniform(1.0, 4.0), wood.uniform(0, 6.3)
      darker = wood.randint(14, 40)
      painter.setPen(QPen(QColor(max(0, colour.red() - darker),
                                 max(0, colour.green() - darker),
                                 max(0, colour.blue() - darker // 2), 90),
                          wood.uniform(0.6, 1.8)))
      last = QPointF(0, at)
      for j in range(1, 33):
        x = SIZE * j / 32
        point = QPointF(x, at + wave * math.sin(2.0 * math.pi * j / 32
                                                + phase))
        painter.drawLine(last, point)
        last = point
    if wood.random() < 0.6:
      knot = QPointF(wood.uniform(30, SIZE - 30), y + 0.5 * high)
      painter.setPen(QPen(QColor(90, 52, 26, 160), 2))
      painter.setBrush(QColor(120, 70, 34, 150))
      painter.drawEllipse(knot, wood.uniform(4, 9), wood.uniform(3, 5))
    painter.setPen(QPen(QColor(48, 28, 14), 3))
    painter.drawLine(QPointF(0, y), QPointF(SIZE, y))
    if staggered:
      cut = (k * 197 + 61) % SIZE
      painter.drawLine(QPointF(cut, y), QPointF(cut, y + high))
  painter.end()
  return image


def pinePainted() -> object:
  """Returns the walls' pine planks: honey pine, running round."""
  return _planks(8, (178, 128, 82), 1975, False)


def boardsPainted() -> object:
  """Returns the floor's oak boards: darker, their ends staggered."""
  return _planks(6, (132, 86, 50), 1976, True)


def rugPainted() -> object:
  """Returns the round braided rag rug: rings of rust, cream, mustard
  and moss round its middle, clear outside it."""
  from PySide6.QtCore import QPointF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(SIZE, SIZE, QImage.Format.Format_ARGB32)
  image.fill(QColor(0, 0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  colours = ((168, 66, 40), (232, 218, 188), (204, 156, 52),
             (96, 112, 64), (126, 48, 34), (222, 204, 170))
  braid = random.Random(1977)
  rings = 22
  middle = QPointF(0.5 * SIZE, 0.5 * SIZE)
  for k in range(rings, 0, -1):
    radius = 0.5 * SIZE * k / rings
    base = colours[k % len(colours)]
    painter.setPen(QPen(QColor(*(max(0, c - 40) for c in base)), 1.5))
    painter.setBrush(QColor(*base))
    painter.drawEllipse(middle, radius, radius)
    painter.setPen(QPen(QColor(*(max(0, c - 25) for c in base), 120), 2))
    for j in range(int(radius * 0.4)):
      a = 2.0 * math.pi * (j + braid.random() * 0.3) / max(1, int(
        radius * 0.4))
      inner, outer = radius - 0.5 * SIZE / rings, radius
      painter.drawLine(QPointF(middle.x() + inner * math.cos(a),
                               middle.y() + inner * math.sin(a)),
                       QPointF(middle.x() + outer * math.cos(a + 0.05),
                               middle.y() + outer * math.sin(a + 0.05)))
  painter.end()
  return image


def blanketPainted() -> object:
  """Returns the knitted blanket: red and cream checks, a row of
  stitches across each."""
  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(SIZE, SIZE, QImage.Format.Format_RGB32)
  painter = QPainter(image)
  red, cream = QColor(176, 40, 36), QColor(236, 226, 206)
  checks = 8
  side = SIZE / checks
  for i in range(checks):
    for j in range(checks):
      painter.fillRect(QRectF(i * side, j * side, side, side),
                       red if (i + j) % 2 else cream)
  painter.setPen(QPen(QColor(0, 0, 0, 40), 2))
  for row in range(0, SIZE, 8):
    for col in range(0, SIZE, 8):
      painter.drawLine(QPointF(col, row + 6), QPointF(col + 4, row + 2))
      painter.drawLine(QPointF(col + 4, row + 2), QPointF(col + 8, row + 6))
  painter.end()
  return image


def glintPainted() -> object:
  """Returns the enchantment glint: soft violet streaks slanting across
  black (black adds nothing where it is laid as a screen)."""
  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
  image = QImage(SIZE, SIZE, QImage.Format.Format_RGB32)
  image.fill(QColor(0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.translate(0.5 * SIZE, 0.5 * SIZE)
  painter.rotate(25.0)
  painter.setPen(QColor(0, 0, 0, 0))
  for start, wide, bright in ((0.05, 0.24, 1.0), (0.38, 0.1, 0.75),
                              (0.6, 0.17, 0.9)):
    for shift in (-2.0, -1.0, 0.0, 1.0):
      x0 = (start + shift) * SIZE
      gradient = QLinearGradient(QPointF(x0, 0), QPointF(x0 + wide * SIZE,
                                                         0))
      gradient.setColorAt(0.0, QColor(0, 0, 0))
      gradient.setColorAt(0.5, QColor(int(205 * bright), int(120 * bright),
                                      int(255 * bright)))
      gradient.setColorAt(1.0, QColor(0, 0, 0))
      painter.setBrush(gradient)
      painter.drawRect(QRectF(x0, -SIZE, wide * SIZE, 2.0 * SIZE))
  painter.end()
  return image


def sparklePainted() -> object:
  """Returns the gravity knob's glint, "lots o glint": violet and pale
  gold streaks slanting both ways across black, twice as many, and
  sparks of light among them (each tiles)."""
  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
  from PySide6.QtGui import QRadialGradient
  image = QImage(SIZE, SIZE, QImage.Format.Format_RGB32)
  image.fill(QColor(0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
  painter.setPen(QColor(0, 0, 0, 0))
  for slant, streaks, tint in ((25.0, ((0.02, 0.2, 1.0), (0.3, 0.08, 0.8),
                                       (0.48, 0.14, 0.95),
                                       (0.74, 0.1, 0.7)), (205, 120, 255)),
                               (-35.0, ((0.12, 0.12, 0.7),
                                        (0.6, 0.16, 0.8)),
                                (255, 214, 140))):
    painter.save()
    painter.translate(0.5 * SIZE, 0.5 * SIZE)
    painter.rotate(slant)
    for start, wide, bright in streaks:
      for shift in (-2.0, -1.0, 0.0, 1.0):
        x0 = (start + shift) * SIZE
        gradient = QLinearGradient(QPointF(x0, 0),
                                   QPointF(x0 + wide * SIZE, 0))
        gradient.setColorAt(0.0, QColor(0, 0, 0))
        gradient.setColorAt(0.5, QColor(*(int(c * bright) for c in tint)))
        gradient.setColorAt(1.0, QColor(0, 0, 0))
        painter.setBrush(gradient)
        painter.drawRect(QRectF(x0, -SIZE, wide * SIZE, 2.0 * SIZE))
    painter.restore()
  sparks = random.Random(1981)
  for _ in range(70):
    x, y = sparks.uniform(0, SIZE), sparks.uniform(0, SIZE)
    radius = sparks.uniform(3.0, 9.0)
    for dx in (-SIZE, 0.0, SIZE):
      for dy in (-SIZE, 0.0, SIZE):
        glow = QRadialGradient(QPointF(x + dx, y + dy), radius)
        glow.setColorAt(0.0, QColor(255, 250, 255))
        glow.setColorAt(0.35, QColor(220, 170, 255))
        glow.setColorAt(1.0, QColor(0, 0, 0))
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(x + dx, y + dy), radius, radius)
  painter.end()
  return image
