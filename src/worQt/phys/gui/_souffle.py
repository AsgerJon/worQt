"""
Soufflé, the tyres' maker (user, 2026-11-14: "we need some soul in
those tires: a funny fictitious tire brand presented with proper racing
tyre writing. ok brand: Soufflé"), as its lettering on a sidewall: one
picture half the way round ('sidewallPicture'), laid twice round each
sidewall ('_meshes._labelRows'), its top outward. The brand in heavy
italic capitals with its mark (a soufflé risen over its ramekin); the
range, 'MERINGUE RS', with the size; the compound, 'SUPER FLUFFY', in
custard, its ring round the tyre as racing tyres mark theirs; the small
print ('NE RETOMBE JAMAIS': it never falls); on the rubber, its fine
ribs by the rim. Painted with Qt (an application must be running: the
fonts).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QImage, QPainter
from PySide6.QtGui import QPainterPath, QPen, QTransform

#  The picture, px: half the sidewall round by across it (its round at
#  the lettering, 0.26 m out, a half 0.81 m, over the sidewall's 81 mm:
#  so a letter is as wide on the tyre as it is drawn).
WIDE, HIGH = 4096, 416
#  The rubber, the letters (white, a little warm), their shadow (raised
#  letters), the custard (the compound's colour) and the mark's crust.
RUBBER = QColor(30, 30, 32)
LETTERS = QColor(238, 236, 228)
SHADOW = QColor(10, 10, 11)
CUSTARD = QColor(240, 196, 70)
CRUST = QColor(196, 132, 58)
#  The faces looked for, the first there taken (Qt falls back on its own
#  sans otherwise); how much wider than drawn the brand is stretched.
FACES = ('Montserrat', 'Adwaita Sans', 'Noto Sans', 'Liberation Sans')
STRETCH = 1.25


def sidewallPicture(path: str) -> None:
  """The 'sidewallPicture' function paints the lettering of half a
  sidewall and saves it at 'path' (a PNG), seamless round: the rubber
  and its ribs, the custard ring by the tread, the brand and its mark
  in the middle, the range and size to the left, the compound and the
  small print to the right."""
  image = QImage(WIDE, HIGH, QImage.Format.Format_RGB888)
  image.fill(RUBBER)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  _rubber(painter)
  painter.fillRect(QRectF(0.0, 0.10 * HIGH, WIDE, 0.03 * HIGH), CUSTARD)
  brand = _faceOf(0.40 * HIGH)
  word = _wordPath('SOUFFLÉ', brand, STRETCH)
  mark = 0.62 * HIGH
  gap = 0.06 * HIGH
  left = 0.5 * (WIDE - (mark + gap + word.boundingRect().width()))
  _mark(painter, QRectF(left, 0.27 * HIGH, mark, 0.47 * HIGH))
  _raised(painter, word, left + mark + gap, 0.71 * HIGH, LETTERS)
  _block(painter, 0.155 * WIDE, (
    ('MERINGUE RS', 0.17, 1.15, LETTERS, 0.48),
    ('205/55 R16 91W', 0.085, 1.1, LETTERS, 0.62),
    ('TUBELESS  ·  RADIAL  ·  DOT SFL 4626', 0.05, 1.1, LETTERS, 0.72)))
  _block(painter, 0.845 * WIDE, (
    ('SUPER FLUFFY', 0.15, 1.15, CUSTARD, 0.46),
    ('NE RETOMBE JAMAIS', 0.075, 1.1, LETTERS, 0.60),
    ('MAX PRESS 350 kPa (51 psi)  ·  CUIT À 180 °C', 0.05, 1.1,
     LETTERS, 0.72)))
  painter.end()
  image.save(path)


def badgePicture(path: str) -> None:
  """The 'badgePicture' function paints the steering wheel's badge and
  saves it at 'path' (a PNG, square, round within): a deep blue disc in
  a custard ring, the soufflé risen over its ramekin, the brand under
  it."""
  size = 512
  image = QImage(size, size, QImage.Format.Format_RGB888)
  image.fill(QColor(18, 18, 20))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(CUSTARD))
  painter.drawEllipse(QRectF(8.0, 8.0, size - 16.0, size - 16.0))
  painter.setBrush(QBrush(QColor(22, 34, 70)))
  painter.drawEllipse(QRectF(34.0, 34.0, size - 68.0, size - 68.0))
  _mark(painter, QRectF(0.31 * size, 0.17 * size, 0.38 * size,
                        0.38 * size))
  word = _wordPath('SOUFFLÉ', _faceOf(0.11 * size), 1.1)
  box = word.boundingRect()
  _raised(painter, word, 0.5 * size - box.left() - 0.5 * box.width(),
          0.75 * size, LETTERS)
  painter.end()
  image.save(path)


def leatherPicture(path: str) -> None:
  """The 'leatherPicture' function paints perforated leather, grey (its
  look's colour times it), seamless, and saves it at 'path': a faint
  grain and rows of small holes, every other row half a hole along."""
  size, pitch = 128, 16
  image = QImage(size, size, QImage.Format.Format_RGB888)
  image.fill(QColor(214, 214, 214))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  random = numpy.random.default_rng(20261115)
  for _ in range(600):
    shade = int(random.integers(196, 232))
    painter.fillRect(QRectF(float(random.uniform(0.0, size)),
                            float(random.uniform(0.0, size)), 2.0, 2.0),
                     QColor(shade, shade, shade))
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QBrush(QColor(70, 70, 70)))
  for row in range(size // pitch):
    for column in range(size // pitch):
      x = (column + 0.5 * (row % 2) + 0.25) * pitch
      y = (row + 0.5) * pitch
      painter.drawEllipse(QPointF(x % size, y), 2.2, 2.2)
  painter.end()
  image.save(path)


def _faceOf(capitals: float) -> QFont:
  """Returns the heavy italic face whose capitals stand 'capitals' px
  (theirs 0.7 of its size)."""
  font = QFont()
  font.setFamilies(list(FACES))
  font.setPixelSize(max(1, round(capitals / 0.7)))
  font.setWeight(QFont.Weight.Black)
  font.setItalic(True)
  return font


def _wordPath(text: str, font: QFont, stretch: float) -> QPainterPath:
  """Returns 'text' in 'font' as an outline, its baseline's start at
  the origin, 'stretch' times as wide."""
  path = QPainterPath()
  path.addText(QPointF(0.0, 0.0), font, text)
  return QTransform.fromScale(stretch, 1.0).map(path)


def _raised(painter: QPainter, path: QPainterPath, x: float, y: float,
            colour: QColor) -> None:
  """Paints 'path' with its baseline's start at 'x', 'y' in 'colour',
  raised: its shadow first, a little down and to the right."""
  for dx, dy, fill in ((4.0, 4.0, SHADOW), (0.0, 0.0, colour)):
    painter.save()
    painter.translate(x + dx, y + dy)
    painter.fillPath(path, QBrush(fill))
    painter.restore()


def _block(painter: QPainter, middle: float, lines: tuple) -> None:
  """Paints 'lines' centred on 'middle', px across: each its text, its
  capitals' height (of the picture's), how much wider it is stretched,
  its colour and where its baseline lies (of the picture's height)."""
  for text, capitals, stretch, colour, base in lines:
    path = _wordPath(text, _faceOf(capitals * HIGH), stretch)
    box = path.boundingRect()
    _raised(painter, path, middle - box.left() - 0.5 * box.width(),
            base * HIGH, colour)


def _mark(painter: QPainter, box: QRectF) -> None:
  """Paints the brand's mark in 'box': a fluted ramekin, white, and the
  soufflé risen straight up out of it, golden, its top hat browned
  (a muffin spills over its rim; a soufflé climbs)."""
  x, y, w, h = box.x(), box.y(), box.width(), box.height()
  rim, foot = y + 0.52 * h, y + h
  dish = QPainterPath()
  dish.moveTo(x + 0.06 * w, rim)
  dish.lineTo(x + 0.94 * w, rim)
  dish.lineTo(x + 0.89 * w, foot)
  dish.lineTo(x + 0.11 * w, foot)
  dish.closeSubpath()
  column = QPainterPath()
  column.addRect(QRectF(x + 0.15 * w, y + 0.2 * h, 0.7 * w, rim - y
                        - 0.2 * h + 0.02 * h))
  hat = QPainterPath()
  hat.moveTo(x + 0.11 * w, y + 0.27 * h)
  hat.cubicTo(x + 0.1 * w, y + 0.02 * h, x + 0.3 * w, y, x + 0.5 * w, y)
  hat.cubicTo(x + 0.7 * w, y, x + 0.9 * w, y + 0.02 * h,
              x + 0.89 * w, y + 0.27 * h)
  hat.closeSubpath()
  for path, fill in ((column, CUSTARD), (hat, CRUST), (dish, LETTERS)):
    painter.save()
    painter.translate(4.0, 4.0)
    painter.fillPath(path, QBrush(SHADOW))
    painter.restore()
    painter.fillPath(path, QBrush(fill))
  pen = QPen(CUSTARD, max(2.0, 0.03 * w))
  pen.setCapStyle(Qt.PenCapStyle.RoundCap)
  painter.setPen(pen)
  painter.drawLine(QPointF(x + 0.3 * w, y + 0.09 * h),
                   QPointF(x + 0.5 * w, y + 0.07 * h))
  pen = QPen(RUBBER, max(2.0, 0.025 * w))
  pen.setCapStyle(Qt.PenCapStyle.RoundCap)
  painter.setPen(pen)
  for k in range(1, 8):
    share = k / 8.0
    top = x + 0.06 * w + share * 0.88 * w
    bottom = x + 0.11 * w + share * 0.78 * w
    painter.drawLine(QPointF(top, rim + 0.1 * h),
                     QPointF(bottom, foot - 0.07 * h))
  painter.setPen(Qt.PenStyle.NoPen)


def _rubber(painter: QPainter) -> None:
  """Paints the rubber's look: a faint mottle, and fine ribs round the
  sidewall by the rim (its lowest fifth)."""
  random = numpy.random.default_rng(20261114)
  for _ in range(1800):
    shade = int(random.integers(24, 38))
    painter.fillRect(QRectF(float(random.uniform(0.0, WIDE)),
                            float(random.uniform(0.0, HIGH)), 3.0, 3.0),
                     QColor(shade, shade, shade + 2))
  pen = QPen(QColor(40, 40, 43), 2.0)
  painter.setPen(pen)
  y = 0.84 * HIGH
  while y < HIGH - 4.0:
    painter.drawLine(QPointF(0.0, y), QPointF(float(WIDE), y))
    y += 9.0
  painter.setPen(Qt.PenStyle.NoPen)
