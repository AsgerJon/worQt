"""
Navball is the artificial horizon (user, 2026-11-16: "we need an
artificial horizon"): a ball of sky over ground turned as the vessel
sees its horizon, its nose in the middle, marks where it travels, where
it came from and where its autopilot aims (the board's, bottom right).
The cabin's globe is honest instead (user, 2026-11-17: "The globus
shaped artificial horizon is 'dishonest'. Right now, the north pole
should point up as we are still parked at the pad"): a ball held level
with the horizon where the rocket is, its pole up, its north north, the
marks where they truly are ('held', 'ways'); its own picture, the
letters reading right from outside ('globeReady').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._looks import cacheFolder
from ._turns import cross, norm, product, quaternionOf, unit, unrotated

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from pathlib import Path

  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  Its picture: its size, pixels (longitude across from the far side,
#  latitude up), the sky's and the ground's colours, the lines'.
WIDE, HIGH = 2048, 1024
SKY, GROUND = '#2f6fb8', '#7a4a22'
LINE, HORIZON = '#e8eef6', '#ffffff'
#  Its pictures' version (a change paints them anew); its numbers' and
#  letters' size, pixels (they were 30 and 56).
VERSION = 2
NUMBERS = 52
LETTERS = 80
#  Its marks: along the path, against it, the aim.
PROGRADE, RETROGRADE, AIM = 'prograde', 'retrograde', 'aim'


class Navball:
  """
  Navball holds the artificial horizon: its picture ('picture', a PNG in
  the looks' cache: painted once, 'pictureReady'), and each frame
  ('frameOf') its turn, its marks, and the nose's pitch and heading.
  The ball's own axes are the horizon's (x east, y north, z up); it is
  turned into the vessel's (y up, z its nose toward the eye), so its
  middle shows where the nose points; and seen as the pilot sees, from
  inside: the vessel's x on the left (from outside a ball is mirrored:
  facing north, east would show on the left). So its mesh is drawn
  mirrored ('mirroredRows': x the other way), its turn mirrored alike (M
  R M, M the mirror: the quaternion's y and z the other way), and a
  mark's x is the vessel's taken the other way.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  picture: Path
  globe: Path

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.picture = cacheFolder() / ('navball-%d.png' % VERSION)
    self.globe = cacheFolder() / ('globe-%d.png' % VERSION)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def pictureReady(self, ) -> Path:
    """The 'pictureReady' method paints the ball's picture if it is not
    kept yet (Qt's painter: its numbers are letters) and returns its
    file."""
    return _kept(self.picture, True)

  def globeReady(self, ) -> Path:
    """The 'globeReady' method paints the cabin's globe's picture (its
    letters reading right from outside) if it is not kept yet and
    returns its file."""
    return _kept(self.globe, False)

  def frameOf(self, vessel: Vessel, system: SolarSystem,
              radius: float) -> dict:
    """The 'frameOf' method returns the ball this frame: its 'turn' (w x
    y z, its own axes to the view's), its 'marks' (each {x, y, kind}:
    pixels from its middle, right and down, for a ball 'radius' pixels
    round; only those on its near side), the nose's 'pitch' and
    'heading' (deg) and which path it shows ('kind': 'orbit' or
    'surface'); the honest globe's turn ('held': the horizon's axes, east
    north up, to the vessel's own) and its marks' ways ('ways': by kind,
    unit vectors in the vessel's own axes)."""
    up, north, east = _horizonOf(vessel, system)
    frame = tuple((east[k], north[k], up[k]) for k in range(3))
    turn = vessel.turn
    seen = product((turn[0], -turn[1], -turn[2], -turn[3]),
                   quaternionOf(frame))
    seen = seen[0], seen[1], -seen[2], -seen[3]
    path = vessel.pathOf(system)
    air = system.bodies[vessel.anchor].air
    kind = 'surface' if air is not None and vessel.heightOver(
      system) < air.top else 'orbit'
    marks = []
    if norm(path) > 1.0:
      way = unit(path)
      marks.append(self._markOf(turn, way, radius, PROGRADE))
      marks.append(self._markOf(turn, tuple(-x for x in way), radius,
                                RETROGRADE))
    if vessel.autopilot.mode == 'aim':
      marks.append(self._markOf(turn, vessel.aimDirection(system), radius,
                                AIM))
    held = product((turn[0], -turn[1], -turn[2], -turn[3]),
                   quaternionOf(frame))
    ways = {}
    if norm(path) > 1.0:
      ways[PROGRADE] = unrotated(turn, unit(path))
      ways[RETROGRADE] = tuple(-x for x in ways[PROGRADE])
    if vessel.autopilot.mode == 'aim':
      ways[AIM] = unrotated(turn, vessel.aimDirection(system))
    pitch, heading = vessel.noseAngles(system)
    return {'turn': seen, 'marks': [m for m in marks if m is not None],
            'pitch': math.degrees(pitch), 'heading': math.degrees(heading),
            'kind': kind, 'held': held, 'ways': ways}

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _markOf(self, turn: tuple, way: tuple, radius: float,
              kind: str) -> dict | None:
    """Returns the mark of 'way' (a unit vector, the ecliptic's) on the
    ball, None on its far side."""
    seen = unrotated(turn, way)
    if seen[2] < 0.0:
      return None
    return {'x': -radius * seen[0], 'y': -radius * seen[1], 'kind': kind}


def _horizonOf(vessel: Vessel, system: SolarSystem) -> tuple:
  """Returns the up, north and east where 'vessel' is."""
  up = unit(vessel.place)
  spin = system.bodies[vessel.anchor].spinVector
  axis = unit(spin) if norm(spin) > 1e-12 else (0.0, 0.0, 1.0)
  east = cross(axis, up)
  if norm(east) < 1e-6:
    east = cross((1.0, 0.0, 0.0), up)
  east = unit(east)
  return up, cross(up, east), east


def _kept(path: Path, mirrored: bool) -> Path:
  """Returns 'path', the picture painted there first if it is not
  kept yet ('mirrored': its letters for a ball drawn mirrored)."""
  if path.exists():
    return path
  path.parent.mkdir(parents=True, exist_ok=True)
  image = _painted(mirrored)
  if not image.save(str(path)):
    raise OSError('the horizon\'s picture could not be kept in %s' % path)
  return path


def _painted(mirrored: bool) -> object:
  """Returns the ball's picture: sky over ground, a line every 10
  degrees of pitch (numbered every 30), the headings every 30 degrees
  (N E S W lettered), its seam on the west; its letters 'mirrored' (for
  a ball drawn mirrored, seen as from inside) or not (seen from
  outside: the cabin's globe), large (user, 2026-11-17: "enlarge the
  font of the numbers on the horizon")."""
  from PySide6.QtCore import QPointF, QRectF, Qt
  from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
  image = QImage(WIDE, HIGH, QImage.Format.Format_RGB32)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  painter.fillRect(QRectF(0, 0, WIDE, HIGH / 2), QColor(SKY))
  painter.fillRect(QRectF(0, HIGH / 2, WIDE, HIGH / 2), QColor(GROUND))

  def rowOf(pitch: float) -> float:
    """Returns the picture's row of 'pitch' (deg)."""
    return (90.0 - pitch) / 180.0 * HIGH

  def written(x: float, y: float, wide: float, high: float,
              text: str) -> None:
    """Writes 'text' centred in the box at 'x', 'y' (mirrored about its
    middle for a ball drawn mirrored: it reads right)."""
    painter.save()
    painter.translate(x + 0.5 * wide, y + 0.5 * high)
    painter.scale(-1.0 if mirrored else 1.0, 1.0)
    painter.drawText(QRectF(-0.5 * wide, -0.5 * high, wide, high),
                     Qt.AlignmentFlag.AlignCenter, text)
    painter.restore()

  def columnOf(heading: float) -> float:
    """Returns the picture's column of the compass 'heading' (deg): its
    longitude from east toward north is 90 less it."""
    lon = (90.0 - heading + 180.0) % 360.0 - 180.0
    return (lon + 180.0) / 360.0 * WIDE

  font = QFont('Sans')
  font.setBold(True)
  for pitch in range(-80, 90, 10):
    if pitch == 0:
      continue
    painter.setPen(QPen(QColor(LINE), 4 if pitch % 30 == 0 else 2))
    painter.drawLine(QPointF(0, rowOf(pitch)), QPointF(WIDE, rowOf(pitch)))
    if pitch % 30 == 0:
      font.setPixelSize(NUMBERS)
      painter.setFont(font)
      for heading in range(0, 360, 90):
        x = columnOf(heading + 45.0)
        written(x - 70, rowOf(pitch) - NUMBERS - 10, 140, NUMBERS + 6,
                '%+d' % pitch)
  for heading in range(0, 360, 30):
    x = columnOf(heading)
    painter.setPen(QPen(QColor(LINE), 3))
    painter.drawLine(QPointF(x, rowOf(80)), QPointF(x, rowOf(-80)))
    letter = {0: 'N', 90: 'E', 180: 'S', 270: 'W'}.get(heading)
    size = LETTERS if letter else NUMBERS
    font.setPixelSize(size)
    painter.setFont(font)
    written(x - 100, rowOf(0) - size - 14, 200, size + 8,
            letter or '%03d' % heading)
  painter.setPen(QPen(QColor(HORIZON), 8))
  painter.drawLine(QPointF(0, rowOf(0)), QPointF(WIDE, rowOf(0)))
  painter.end()
  return image


def mirroredRows(rows: object) -> object:
  """Returns a sphere's rows ('_meshes.sphereRows') mirrored: places and
  normals with x the other way, where on the picture each lies kept."""
  out = rows.copy()
  out[:, 0] = -out[:, 0]
  out[:, 3] = -out[:, 3]
  return out
