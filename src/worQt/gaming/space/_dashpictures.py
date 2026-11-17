"""
The dashboard's pictures, painted once (Qt's painter: letters) and kept
in the looks' cache: the panel's brushed face with its legends printed
(the dials' and lamps' names, the switches', the warp knob's scale, the
deck's and the monitor's), the dials' faces (black, amber numerals backlit,
their scales a logarithm's), the labels (the switches' legends in amber
on smoked glass, the keys' caps in black on aluminium with their keys).
1970s B&O in spirit: its look only, no name or mark of theirs (the
corner carries worQt's own).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import CONSOLE_KEYS, DECK_KEYS, DIALS, DIAL_RADIUS, KEYS
from ._cockpit import KNOBS
from ._cockpit import KNOB_RADIUS, LAMPS, PANEL_HALF, SWITCHES
from ._cockpit import SECTIONS
from ._ascentguidance import TARGETS
from ._dashboard import DIAL_SCALES, LEGENDS, dialAngle, dialShare
from ._looks import cacheFolder

#  The pictures' versions (a change paints them anew) and sizes, pixels.
VERSION = 12
FACE = (2048, 1280)
DIAL = 512
CELL = (256, 128)
CELLS = 6
#  The warp knob's notches, as printed round it.
WARP_MARKS = ('1', '5', '10', '50', '100', '1K', '10K', '100K')
#  The orbit knob's notches, as printed round it: the guidance's targets,
#  km.
ORBIT_MARKS = tuple('%d' % (target / 1e3) for target in TARGETS)
#  The engine's limiter's notches, g (user, 2026-11-17: "restricts the
#  engine output to a particular g, for example 1").
LIMIT_MARKS = ('\u00bc', '\u00bd', '\u00be', '1', '1\u00bd', '2', '3',
               '4')
#  Each knob's marks and its unit, by its action.
KNOB_MARKS = {'warp': (WARP_MARKS, ''), 'orbit': (ORBIT_MARKS, '  KM'),
              'limit': (LIMIT_MARKS, '  G')}
#  The keys' faces' names (the panel's and the consoles').
KEY_NAMES = tuple(name for name, _, _, _ in KEYS + CONSOLE_KEYS
                  + DECK_KEYS)
#  The keys' symbols (the deck's).
SYMBOLS = {'PLAY': '▶', 'STOP': '■', 'EJECT': '⏏', 'UP': '▲',
           'DOWN': '▼', 'LEFT': '◀', 'RIGHT': '▶'}


def picturesReady() -> dict:
  """Returns the dashboard's pictures' files ('face', 'dials', 'labels',
  'glass': the horizon's cover, 'marks': its marks' decals, 'wood': the
  monitor's veneer), painted if not kept yet, and where each label lies
  on the labels' picture ('cells': by name, u0, v0, u1, v1 from its
  bottom left)."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  out = {}
  for name, painter in (('face', facePainted), ('dials', dialsPainted),
                        ('labels', labelsPainted), ('glass', glassPainted),
                        ('marks', marksPainted), ('wood', woodPainted)):
    target = folder / ('dash-%s-%d.png' % (name, VERSION))
    if not target.exists() and not painter().save(str(target)):
      raise OSError('the picture %s could not be kept in %s' % (name,
                                                               target))
    out[name] = target
  out['cells'] = labelCells()
  return out


def labelCells() -> dict:
  """Returns where each label lies on the labels' picture, by name (a
  cell each: more than its 'CELLS' rows of 'CELLS' raise)."""
  names = LEGENDS + KEY_NAMES
  if len(names) > CELLS * CELLS:
    raise ValueError('%d labels, the picture holds %d' % (
      len(names), CELLS * CELLS))
  out = {}
  for k, name in enumerate(names):
    column, row = k % CELLS, k // CELLS
    out[name] = (column / CELLS, 1.0 - (row + 1) / CELLS,
                 (column + 1) / CELLS, 1.0 - row / CELLS)
  return out


def _faceXY(right: float, up: float) -> tuple:
  """Returns the face picture's pixel at 'right', 'up' m on the panel."""
  return ((right + PANEL_HALF[0]) / (2 * PANEL_HALF[0]) * FACE[0],
          (PANEL_HALF[1] - up) / (2 * PANEL_HALF[1]) * FACE[1])


def _metres(far: float) -> float:
  """Returns 'far' m in the face picture's pixels."""
  return far / (2 * PANEL_HALF[0]) * FACE[0]


def facePainted() -> object:
  """Returns the panel's face: brushed aluminium, its zones grooved, its
  legends printed in black."""
  import random

  from PySide6.QtCore import QPointF, QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
  image = QImage(FACE[0], FACE[1], QImage.Format.Format_RGB32)
  image.fill(QColor(196, 198, 201))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  streaks = random.Random(1970)
  for _ in range(5000):
    y = streaks.uniform(0, FACE[1])
    shade = streaks.randint(178, 216)
    painter.setPen(QPen(QColor(shade, shade, shade + 2, 90), 1))
    x = streaks.uniform(-200, FACE[0])
    painter.drawLine(QPointF(x, y), QPointF(x + streaks.uniform(200, 900),
                                            y))

  def text(right: float, up: float, words: str, size: float,
           colour: str = '#1c1c1e', bold: bool = True) -> None:
    """Prints 'words' centred at 'right', 'up' m, 'size' m high."""
    font = QFont('Sans')
    font.setBold(bold)
    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
    font.setPixelSize(max(6, int(_metres(size))))
    painter.setFont(font)
    painter.setPen(QColor(colour))
    x, y = _faceXY(right, up)
    wide = _metres(0.12)
    painter.drawText(QRectF(x - wide, y - _metres(size), 2 * wide,
                            2 * _metres(size)), Qt.AlignmentFlag.AlignCenter,
                     words)

  for title, left, bottom, right, top in SECTIONS:
    x0, y0 = _faceXY(left, top)
    x1, y1 = _faceXY(right, bottom)
    painter.setPen(QPen(QColor(92, 94, 98), 3))
    painter.setBrush(QColor(180, 182, 186, 70))
    painter.drawRoundedRect(QRectF(x0, y0, x1 - x0, y1 - y0), 14, 14)
    font = QFont('Sans')
    font.setBold(True)
    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 125)
    font.setPixelSize(int(_metres(0.0085)))
    painter.setFont(font)
    painter.setPen(QColor('#2a2a2e'))
    painter.drawText(QRectF(x0 + _metres(0.008), y0 + _metres(0.003),
                            x1 - x0, _metres(0.014)),
                     Qt.AlignmentFlag.AlignLeft
                     | Qt.AlignmentFlag.AlignVCenter, title)
  for name, (u, v) in DIALS:
    unit = DIAL_SCALES[name][3]
    text(u, v - DIAL_RADIUS - 0.012, '%s  %s' % (name, unit), 0.009)
  for name, (u, v) in LAMPS:
    text(u, v - 0.016, name, 0.0055)
  for name, key, _, (u, v) in SWITCHES:
    text(u, v - 0.032, 'ON  %s' % key, 0.0055, '#3a3a3e', False)
  for name, key, action, (u, v), notches, near, step in KNOBS:
    marks, unit = KNOB_MARKS[action]
    text(u, v - KNOB_RADIUS - 0.024, '%s%s  %s' % (name, unit, key),
         0.0075)
    painter.setPen(QPen(QColor('#1c1c1e'), 4))
    for k, mark in enumerate(marks[:notches]):
      angle = near + k * step
      inner, outer = KNOB_RADIUS + 0.003, KNOB_RADIUS + 0.008
      painter.drawLine(QPointF(*_faceXY(u + inner * math.sin(-angle),
                                        v + inner * math.cos(angle))),
                       QPointF(*_faceXY(u + outer * math.sin(-angle),
                                        v + outer * math.cos(angle))))
      reach = KNOB_RADIUS + 0.016
      text(u + reach * math.sin(-angle), v + reach * math.cos(angle),
           mark, 0.0062)
  for name, key, _, (u, v) in KEYS:
    if name in SYMBOLS:
      continue
    text(u, v - 0.026, key, 0.0055, '#3a3a3e', False)
  text(0.0, -0.243, 'worQt', 0.008, '#55575c', False)
  painter.end()
  return image


def dialsPainted() -> object:
  """Returns the dials' faces, four across: black, amber ticks and
  numerals backlit, a tick at every tenfold and four between."""
  from PySide6.QtCore import QPointF, QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
  image = QImage(DIAL * len(DIALS), DIAL, QImage.Format.Format_RGB32)
  image.fill(QColor(16, 14, 12))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  amber = QColor(255, 176, 64)
  font = QFont('Sans')
  font.setBold(True)
  for k, (name, _) in enumerate(DIALS):
    cx, cy = (k + 0.5) * DIAL, 0.5 * DIAL
    turn, most, ticks, unit = DIAL_SCALES[name]

    def point(share: float, radius: float) -> QPointF:
      """Returns the face's point at 'share' of the scale, 'radius' px
      out."""
      a = dialAngle(share)
      return QPointF(cx + radius * math.sin(a), cy - radius * math.cos(a))

    for decade in range(len(ticks) - 1):
      low, high = ticks[decade][0], ticks[decade + 1][0]
      for step in range(1, 10):
        value = low + (high - low) * step / 10.0
        share = dialShare(name, value)
        painter.setPen(QPen(amber, 3))
        painter.drawLine(point(share, 0.42 * DIAL),
                         point(share, 0.46 * DIAL))
    for value, words in ticks:
      share = dialShare(name, value)
      painter.setPen(QPen(amber, 8))
      painter.drawLine(point(share, 0.38 * DIAL), point(share, 0.47 * DIAL))
      font.setPixelSize(int(0.085 * DIAL))
      painter.setFont(font)
      at = point(share, 0.29 * DIAL)
      painter.drawText(QRectF(at.x() - 70, at.y() - 30, 140, 60),
                       Qt.AlignmentFlag.AlignCenter, words)
    font.setPixelSize(int(0.06 * DIAL))
    painter.setFont(font)
    painter.setPen(QColor(200, 140, 60))
    painter.drawText(QRectF(cx - 150, cy + 0.12 * DIAL, 300, 60),
                     Qt.AlignmentFlag.AlignCenter, unit)
  painter.end()
  return image


def labelsPainted() -> object:
  """Returns the labels: the switches' legends (amber letters on smoked
  glass: lit by their lamps), the keys' caps (black on aluminium, the
  key that does the same in a small cap)."""
  from PySide6.QtCore import QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
  image = QImage(CELL[0] * CELLS, CELL[1] * CELLS,
                 QImage.Format.Format_RGB32)
  image.fill(QColor(30, 30, 32))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  font = QFont('Sans')
  font.setBold(True)
  keys = {name: key for name, key, _, _ in KEYS + CONSOLE_KEYS + DECK_KEYS}
  for k, name in enumerate(LEGENDS + KEY_NAMES):
    x, y = (k % CELLS) * CELL[0], (k // CELLS) * CELL[1]
    cell = QRectF(x, y, CELL[0], CELL[1])
    if name in LEGENDS:
      painter.fillRect(cell, QColor(36, 22, 10))
      font.setPixelSize(52)
      painter.setFont(font)
      painter.setPen(QColor(255, 178, 70))
      painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, name)
      continue
    painter.fillRect(cell, QColor(208, 210, 213))
    font.setPixelSize(40 if name not in SYMBOLS else 54)
    painter.setFont(font)
    painter.setPen(QColor(24, 24, 26))
    painter.drawText(QRectF(x, y + 6, CELL[0], 70),
                     Qt.AlignmentFlag.AlignCenter,
                     SYMBOLS.get(name, name))
    key = keys[name]
    font.setPixelSize(26)
    painter.setFont(font)
    wide = max(44, 20 * len(key) + 22)
    cap = QRectF(x + 0.5 * (CELL[0] - wide), y + 78, wide, 38)
    painter.setPen(QPen(QColor(110, 112, 118), 3))
    painter.setBrush(QColor(236, 238, 240))
    painter.drawRoundedRect(cap, 7, 7)
    painter.setPen(QColor(24, 24, 26))
    painter.drawText(cap, Qt.AlignmentFlag.AlignCenter, key)
  painter.end()
  return image


#  The horizon's marks' decals, in this order across their picture.
MARK_NAMES = ('prograde', 'retrograde', 'aim')
#  Sizes: the glass's picture, a mark's cell, the veneer's, pixels.
GLASS_SIZE = 512
MARK_CELL = 128
WOOD = (512, 512)


def glassPainted() -> object:
  """Returns the horizon's glass cover's picture (user, 2026-11-16: "The
  two yellow lines on the horizon has to be replaced. maybe with glass
  cover over the ball that has them painted on?"): clear but a breath
  of tint, the reference painted in amber (two wings, their tips down,
  a dot in the middle), ticks round its rim every 30 degrees of roll, a
  window's glint up on its left."""
  from PySide6.QtCore import QPointF, QRectF, Qt
  from PySide6.QtGui import (QColor, QImage, QPainter, QPainterPath, QPen,
                             QRadialGradient)
  size = GLASS_SIZE
  image = QImage(size, size, QImage.Format.Format_ARGB32)
  image.fill(QColor(0, 0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  middle = QPointF(0.5 * size, 0.5 * size)
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(QColor(200, 215, 230, 14))
  painter.drawEllipse(middle, 0.5 * size, 0.5 * size)
  glint = QRadialGradient(QPointF(0.33 * size, 0.27 * size), 0.22 * size)
  glint.setColorAt(0.0, QColor(255, 255, 255, 70))
  glint.setColorAt(1.0, QColor(255, 255, 255, 0))
  painter.setBrush(glint)
  painter.drawEllipse(QPointF(0.33 * size, 0.27 * size), 0.22 * size,
                      0.12 * size)
  amber = QColor(255, 168, 30, 245)
  pen = QPen(amber, 0.022 * size)
  pen.setCapStyle(Qt.PenCapStyle.RoundCap)
  pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
  painter.setPen(pen)
  painter.setBrush(Qt.BrushStyle.NoBrush)
  for side in (-1.0, 1.0):
    wing = QPainterPath(QPointF(middle.x() + side * 0.08 * size, middle.y()))
    wing.lineTo(middle.x() + side * 0.25 * size, middle.y())
    wing.lineTo(middle.x() + side * 0.25 * size, middle.y() + 0.04 * size)
    painter.drawPath(wing)
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(amber)
  painter.drawEllipse(middle, 0.022 * size, 0.022 * size)
  painter.setPen(QPen(QColor(255, 255, 255, 150), 0.008 * size))
  for k in range(12):
    angle = math.radians(30.0 * k)
    inner, outer = 0.43 * size, 0.47 * size
    painter.drawLine(QPointF(middle.x() + inner * math.sin(angle),
                             middle.y() - inner * math.cos(angle)),
                     QPointF(middle.x() + outer * math.sin(angle),
                             middle.y() - outer * math.cos(angle)))
  painter.setPen(QPen(QColor(20, 20, 22, 160), 0.012 * size))
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.drawEllipse(QRectF(0.006 * size, 0.006 * size, 0.988 * size,
                             0.988 * size))
  painter.end()
  return image


def marksPainted() -> object:
  """Returns the horizon's marks' decals, painted on the ball, three
  across ('MARK_NAMES'): prograde a green ring with a dot and three
  ticks, retrograde a green ring crossed, the aim a pink diamond round
  a dot; clear round them."""
  from PySide6.QtCore import QPointF, Qt
  from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPolygonF
  cell = MARK_CELL
  image = QImage(cell * len(MARK_NAMES), cell, QImage.Format.Format_ARGB32)
  image.fill(QColor(0, 0, 0, 0))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  green, pink = QColor(150, 240, 60), QColor(255, 90, 200)
  for k, name in enumerate(MARK_NAMES):
    x = (k + 0.5) * cell
    y = 0.5 * cell
    colour = pink if name == 'aim' else green
    pen = QPen(colour, 0.075 * cell)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name == 'aim':
      painter.drawPolygon(QPolygonF([QPointF(x, y - 0.36 * cell),
                                     QPointF(x + 0.36 * cell, y),
                                     QPointF(x, y + 0.36 * cell),
                                     QPointF(x - 0.36 * cell, y)]))
    else:
      painter.drawEllipse(QPointF(x, y), 0.24 * cell, 0.24 * cell)
    if name == 'prograde':
      for dx, dy in ((0.0, -1.0), (-1.0, 0.0), (1.0, 0.0)):
        painter.drawLine(QPointF(x + 0.24 * cell * dx, y + 0.24 * cell * dy),
                         QPointF(x + 0.42 * cell * dx, y + 0.42 * cell * dy))
    if name == 'retrograde':
      for dx, dy in ((1.0, 1.0), (1.0, -1.0)):
        painter.drawLine(QPointF(x - 0.17 * cell * dx, y - 0.17 * cell * dy),
                         QPointF(x + 0.17 * cell * dx, y + 0.17 * cell * dy))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(colour)
    if name != 'retrograde':
      painter.drawEllipse(QPointF(x, y), 0.06 * cell, 0.06 * cell)
  painter.end()
  return image


def woodPainted() -> object:
  """Returns the monitor cabinet's veneer (user, 2026-11-16: "The CCTV
  should have more of a fake wood feel to it"): a 1970s printed
  walnut, its grain running across, a little too even."""
  import random

  from PySide6.QtCore import QPointF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(WOOD[0], WOOD[1], QImage.Format.Format_RGB32)
  image.fill(QColor(96, 58, 32))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  grain = random.Random(1974)
  for _ in range(260):
    y = grain.uniform(0, WOOD[1])
    wave = grain.uniform(3.0, 14.0)
    length = grain.uniform(60.0, 180.0)
    shade = grain.randint(-26, 18)
    colour = QColor(max(0, 96 + shade), max(0, 58 + shade // 2),
                    max(0, 32 + shade // 3), grain.randint(60, 150))
    painter.setPen(QPen(colour, grain.uniform(1.0, 4.0)))
    last = QPointF(0.0, y)
    for k in range(1, 41):
      x = WOOD[0] * k / 40.0
      point = QPointF(x, y + wave * math.sin(x / length + y))
      painter.drawLine(last, point)
      last = point
  painter.end()
  return image
