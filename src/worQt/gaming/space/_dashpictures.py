"""
The dashboard's pictures, painted once (Qt's painter: letters) and kept
in the looks' cache: the panel's brushed face curved round him with its
legends printed (its sections, the knobs' scales, the keys' keys, the
throttle's scale), the hood's (the dials' and lamps' names, Terra
Prime's range's), the dials' faces (black, amber numerals backlit,
their scales a logarithm's), the labels (the lit keys' and the
switches' legends in amber on smoked glass, the keys' caps in black on
aluminium with their keys). 1970s B&O in spirit: its look only, no
name or mark of theirs (the corner carries worQt's own).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from ._cockpit import CAPS, CONSOLE_KEYS, DECK_KEYS, DIALS, DIAL_RADIUS
from ._cockpit import FACE_HIGH, FACE_LOW, FRAME, GLOBE_ON, HOOD_HIGH
from ._cockpit import HOOD_RADIUS, HOOD_SPAN, KEYS, KNOBS, KNOB_RADIUS
from ._cockpit import LAMPS, LIT_KEYS, PANEL_RADIUS, PANEL_SPAN
from ._cockpit import PAPER_AT, PAPER_HIGH, PAPER_WIDE, RANGE, SCREEN_AT
from ._cockpit import SCREEN_HALF, SECTIONS, STATUS, THROTTLE_AT
from ._cockpit import THROTTLE_LONG, panelWide
from ._ascentguidance import TARGETS
from ._dashboard import DIAL_SCALES, LEGENDS, dialAngle, dialShare
from ._dashboard import readoutLayout
from ._looks import cacheFolder

#  The pictures' versions (a change paints them anew) and sizes, pixels:
#  the face's across and up (as many a metre each way along its middle
#  line and up its slant), the hood's, a dial's, a label's cell.
VERSION = 15
FACE_ACROSS = 2.0 * PANEL_RADIUS * PANEL_SPAN
HOOD_ACROSS = 2.0 * HOOD_RADIUS * HOOD_SPAN
FACE = (4096, round(4096 * (FACE_HIGH - FACE_LOW) / FACE_ACROSS))
HOOD = (2048, round(2048 * HOOD_HIGH / HOOD_ACROSS))
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
#  The keys' faces' names: the panel's (but the lit ones: 'LEGENDS'),
#  the consoles' and the deck's (the deck's and the console's tape keys
#  share theirs).
KEY_NAMES = tuple(dict.fromkeys(
  [key[0] for key in KEYS if key[0] not in LIT_KEYS]
  + [key[0] for key in CONSOLE_KEYS + DECK_KEYS]))
#  The keys' symbols (the deck's, the thrusters').
SYMBOLS = {'PLAY': '\u25b6', 'STOP': '\u25a0', 'EJECT': '\u23cf',
           'UP': '\u25b2', 'DOWN': '\u25bc', 'LEFT': '\u25c0',
           'RIGHT': '\u25b6'}
#  What is printed under the AUTOPILOT's two numbered keys.
STEPS_SAID = {'ASCENT': 'TO ORBIT', 'RNDZ': 'TO TERRA PRIME'}


def picturesReady() -> dict:
  """Returns the dashboard's pictures' files ('face', 'hood', 'dials',
  'labels', 'glass': the horizon's cover, 'marks': its marks' decals,
  'wood': the monitor's veneer), painted if not kept yet, and where each
  label lies on the labels' picture ('cells': by name, u0, v0, u1, v1
  from its bottom left)."""
  folder = cacheFolder()
  folder.mkdir(parents=True, exist_ok=True)
  out = {}
  for name, painter in (('face', facePainted), ('hood', hoodPainted),
                        ('dials', dialsPainted), ('labels', labelsPainted),
                        ('glass', glassPainted), ('marks', marksPainted),
                        ('wood', woodPainted)):
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


class _Print:
  """
  _Print prints on a curved sheet's picture (the panel's face, the
  hood's) at places along its middle line ('right', m from its middle)
  and up its slant ('up', m from its 'low' edge): each thing about its
  own middle in true metres, the picture's squeeze at its height undone
  ('wide': how much wider the sheet is there than along its middle
  line).
  """

  def __init__(self, painter: object, size: tuple, across: float,
               low: float, high: float, wide: object) -> None:
    self.painter, self.size, self.across = painter, size, across
    self.low, self.high, self.wide = low, high, wide

  def at(self, right: float, up: float) -> tuple:
    """Returns the picture's pixel at 'right', 'up'."""
    return ((right + 0.5 * self.across) / self.across * self.size[0],
            (self.high - up) / (self.high - self.low) * self.size[1])

  def metres(self, far: float) -> float:
    """Returns 'far' m in the picture's pixels."""
    return far / self.across * self.size[0]

  def about(self, right: float, up: float) -> None:
    """Moves the painter to 'right', 'up', its squeeze undone (paint in
    true metres from there: 'metres'); 'done' moves it back."""
    self.painter.save()
    self.painter.translate(*self.at(right, up))
    self.painter.scale(1.0 / self.wide(up), 1.0)

  def done(self, ) -> None:
    """Moves the painter back."""
    self.painter.restore()

  def text(self, right: float, up: float, words: str, size: float,
           colour: str = '#1c1c1e', bold: bool = True) -> None:
    """Prints 'words' centred at 'right', 'up', 'size' m high."""
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QColor, QFont
    font = QFont('Sans')
    font.setBold(bold)
    font.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 112)
    font.setPixelSize(max(6, int(self.metres(size))))
    self.painter.setFont(font)
    self.painter.setPen(QColor(colour))
    self.about(right, up)
    wide, high = self.metres(0.12), self.metres(size)
    self.painter.drawText(QRectF(-wide, -high, 2 * wide, 2 * high),
                          Qt.AlignmentFlag.AlignCenter, words)
    self.done()


def _brushed(painter: object, size: tuple, seed: int) -> None:
  """Paints brushed aluminium over a picture of 'size'."""
  import random

  from PySide6.QtCore import QPointF
  from PySide6.QtGui import QColor, QPen
  painter.fillRect(0, 0, size[0], size[1], QColor(196, 198, 201))
  streaks = random.Random(seed)
  for _ in range(int(3 * size[0] * size[1] / 2048)):
    y = streaks.uniform(0, size[1])
    shade = streaks.randint(178, 216)
    painter.setPen(QPen(QColor(shade, shade, shade + 2, 90), 1))
    x = streaks.uniform(-200, size[0])
    painter.drawLine(QPointF(x, y), QPointF(x + streaks.uniform(200, 900),
                                            y))


def _rosewood(painter: object, x: float, y: float, wide: float,
              high: float) -> None:
  """Paints a band of rosewood: dark red brown, its grain along it."""
  import random

  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QLinearGradient, QPen
  shade = QLinearGradient(QPointF(x, y), QPointF(x, y + high))
  shade.setColorAt(0.0, QColor(96, 40, 26))
  shade.setColorAt(1.0, QColor(52, 18, 11))
  painter.fillRect(QRectF(x, y, wide, high), shade)
  grain = random.Random(int(x + 7 * y))
  for _ in range(max(2, int(high / 3))):
    at = grain.uniform(y, y + high)
    painter.setPen(QPen(QColor(24, 8, 4, 90), 1))
    painter.drawLine(QPointF(x, at), QPointF(x + wide, at + grain.uniform(
      -2, 2)))


def facePainted() -> object:
  """Returns the panel's face (curved round him: printed along its
  middle line and up its slant, each thing true to size where it is):
  brushed aluminium in a rosewood border, its sections framed and
  titled, the keys' keys under them, the knobs' scales, the throttle's,
  dark windows round the status line and the teleprinter's paper."""
  from PySide6.QtCore import QPointF, QRectF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(FACE[0], FACE[1], QImage.Format.Format_RGB32)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  _brushed(painter, FACE, 1970)
  sheet = _Print(painter, FACE, FACE_ACROSS, FACE_LOW, FACE_HIGH, panelWide)
  border = sheet.metres(FRAME)
  _rosewood(painter, 0, 0, FACE[0], border)
  _rosewood(painter, 0, FACE[1] - border, FACE[0], border)
  _rosewood(painter, 0, 0, border, FACE[1])
  _rosewood(painter, FACE[0] - border, 0, border, FACE[1])
  for title, left, bottom, right, top in SECTIONS:
    x0, y0 = sheet.at(left, top)
    x1, y1 = sheet.at(right, bottom)
    painter.setPen(QPen(QColor(92, 94, 98), 4))
    painter.setBrush(QColor(180, 182, 186, 70))
    painter.drawRoundedRect(QRectF(x0, y0, x1 - x0, y1 - y0), 20, 20)
    sheet.text(left + 0.01 + 0.004 * len(title), top - 0.011, title,
               0.0095)
  for (u, v), (hw, hh), margin in ((STATUS[0], STATUS[1], 0.004),
                                   (PAPER_AT, (0.5 * PAPER_WIDE,
                                               0.5 * PAPER_HIGH), 0.004)):
    x0, y0 = sheet.at(u - hw - margin, v + hh + margin)
    x1, y1 = sheet.at(u + hw + margin, v - hh - margin)
    painter.setPen(QPen(QColor(60, 60, 62), 3))
    painter.setBrush(QColor(22, 20, 18))
    painter.drawRoundedRect(QRectF(x0, y0, x1 - x0, y1 - y0), 10, 10)
  for name, key, action, (u, v), half in KEYS:
    sheet.text(u, v - half[1] - 0.009, key, 0.0062, '#3a3a3e', False)
    if name in STEPS_SAID:
      sheet.text(u, v + half[1] + 0.009, STEPS_SAID[name], 0.0065)
  sheet.text(-0.362, 0.061, 'ATTITUDE', 0.0065)
  sheet.text(0.475, 0.115, 'THRUSTERS', 0.0065)
  sheet.text(SCREEN_AT[0], SCREEN_AT[1] - SCREEN_HALF[1] - 0.026, 'CCTV',
             0.0065)
  for name, key, action, (u, v), notches, near, step in KNOBS:
    marks, unit = KNOB_MARKS[action]
    sheet.text(u, v - KNOB_RADIUS - 0.026, '%s%s  %s' % (name, unit, key),
               0.0075)
    for k, mark in enumerate(marks[:notches]):
      angle = near + k * step
      sheet.about(u, v)
      painter.setPen(QPen(QColor('#1c1c1e'), 4))
      inner, outer = KNOB_RADIUS + 0.003, KNOB_RADIUS + 0.008
      painter.drawLine(QPointF(sheet.metres(inner * math.sin(-angle)),
                               -sheet.metres(inner * math.cos(angle))),
                       QPointF(sheet.metres(outer * math.sin(-angle)),
                               -sheet.metres(outer * math.cos(angle))))
      sheet.done()
      reach = KNOB_RADIUS + 0.016
      wide = panelWide(v)
      sheet.text(u + reach * math.sin(-angle) / wide,
                 v + reach * math.cos(angle), mark, 0.0062)
  u, v = THROTTLE_AT
  for k in range(5):
    at = v + THROTTLE_LONG * k / 4.0
    sheet.about(u, at)
    painter.setPen(QPen(QColor('#1c1c1e'), 4))
    painter.drawLine(QPointF(-sheet.metres(0.024), 0.0),
                     QPointF(-sheet.metres(0.012), 0.0))
    sheet.done()
    sheet.text(u - 0.036 / panelWide(at), at, '%d' % (25 * k), 0.0065)
  sheet.text(u, v - 0.024, 'THRUST %', 0.0075)
  sheet.text(u, v - 0.036, '+  \u2212', 0.0062, '#3a3a3e', False)
  sheet.text(GLOBE_ON[0] + 0.66, FACE_LOW + 0.006, 'worQt', 0.007,
             '#d8b8a0', False)
  painter.end()
  return image


def hoodPainted() -> object:
  """Returns the hood's face: a dark instrument strip in a rosewood
  border, the dials' names under them, the lamps' under theirs, a dark
  window round Terra Prime's range and its groups' labels."""
  from PySide6.QtCore import QRectF
  from PySide6.QtGui import QColor, QImage, QPainter, QPen
  image = QImage(HOOD[0], HOOD[1], QImage.Format.Format_RGB32)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  sheet = _Print(painter, HOOD, HOOD_ACROSS, 0.0, HOOD_HIGH,
                 lambda up: 1.0)
  _rosewood(painter, 0, 0, HOOD[0], HOOD[1])
  border = sheet.metres(FRAME)
  painter.setPen(QPen(QColor(10, 10, 10), 3))
  painter.setBrush(QColor(20, 19, 18))
  painter.drawRoundedRect(QRectF(border, border, HOOD[0] - 2 * border,
                                 HOOD[1] - 2 * border), 24, 24)
  pale = '#d8c8b0'
  for name, (u, v) in DIALS:
    unit = DIAL_SCALES[name][3]
    sheet.text(u, v - DIAL_RADIUS - 0.012, '%s  %s' % (name, unit), 0.0068,
               pale)
  for name, (u, v) in LAMPS:
    sheet.text(u, v - 0.014, name, 0.0048, pale)
  (u, v), (hw, hh) = RANGE
  x0, y0 = sheet.at(u - hw - 0.004, v + hh + 0.004)
  x1, y1 = sheet.at(u + hw + 0.004, v - hh - 0.004)
  painter.setPen(QPen(QColor(70, 60, 50), 3))
  painter.setBrush(QColor(8, 6, 5))
  painter.drawRoundedRect(QRectF(x0, y0, x1 - x0, y1 - y0), 12, 12)
  sheet.text(u, v + hh + 0.011, 'TERRA PRIME', 0.0068, pale)
  layout = readoutLayout()
  for group in layout['groups']:
    middle = group['from'] + 0.5 * group['tubes'] * group['tube']
    sheet.text(u - hw + 2.0 * hw * middle / layout['width'],
               v - hh - 0.008, group['label'], 0.0052, pale)
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
  """Returns the labels: the lit keys' caps and the switches' legends
  (amber letters on smoked glass: lit by their lamps), the keys' caps
  (black on aluminium, the key that does the same in a small cap)."""
  from PySide6.QtCore import QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
  image = QImage(CELL[0] * CELLS, CELL[1] * CELLS,
                 QImage.Format.Format_RGB32)
  image.fill(QColor(30, 30, 32))
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  font = QFont('Sans')
  font.setBold(True)
  keys = {key[0]: key[1] for key in KEYS + CONSOLE_KEYS + DECK_KEYS}
  for k, name in enumerate(LEGENDS + KEY_NAMES):
    x, y = (k % CELLS) * CELL[0], (k // CELLS) * CELL[1]
    cell = QRectF(x, y, CELL[0], CELL[1])
    words = CAPS.get(name, name)
    lines = words.count('\n') + 1
    if name in LEGENDS:
      painter.fillRect(cell, QColor(36, 22, 10))
      font.setPixelSize(52 if lines == 1 else 40)
      painter.setFont(font)
      painter.setPen(QColor(255, 178, 70))
      painter.drawText(cell, Qt.AlignmentFlag.AlignCenter, words)
      continue
    painter.fillRect(cell, QColor(208, 210, 213))
    font.setPixelSize(54 if name in SYMBOLS else (40 if lines == 1
                                                  else 30))
    painter.setFont(font)
    painter.setPen(QColor(24, 24, 26))
    painter.drawText(QRectF(x, y + 6, CELL[0], 70),
                     Qt.AlignmentFlag.AlignCenter,
                     SYMBOLS.get(name, words))
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
  """Returns the horizon's glass cover's picture: clear but a breath of
  tint, a window's glint up on its left, its rim (its amber wings, dot
  and roll ticks are gone: user, 2026-11-17, "The yellow markers need
  to disappear": the globe is held level with the horizon, not turned
  to the nose, so a reference on its glass marked nothing)."""
  from PySide6.QtCore import QPointF, QRectF, Qt
  from PySide6.QtGui import QColor, QImage, QPainter, QPen, QRadialGradient
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
