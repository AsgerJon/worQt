"""
The cabin's meshes, in the vessel's own axes ('_cockpit' has where
everything is): the capsule's skin and its inner wall with the windows
cut through both (from outside you see Asger through the glass), the
glass, the floor and the ceiling, the seat, the consoles' rosewood and
their aluminium tops. The dashboard on them is '_dashboard''s. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._cockpit import BACKREST, CUSHION, FLOOR, LEFT_CONSOLE, NOSE
from ._cockpit import RIGHT_CONSOLE, WALL, WINDOWS, capsuleRadius
from ._cabinpictures import BOARD_TILE, PINE_TILE
from ._vessel import SIZE

#  The cone's round in steps of this many degrees (the windows' edges
#  fall on them), its heights at least every 'STOREY' m and at every
#  window's edge.
STEP = 2.0
STOREY = 0.2


def capsuleShell(inner: bool) -> tuple:
  """Returns the capsule's skin (its nose, and the windows' jambs through
  the wall) or, 'inner', its inner wall (and the ceiling), the windows
  cut through both: rows (place, normal) and triangles."""
  heights = sorted({FLOOR, NOSE} | {z for _, span in WINDOWS for z in span}
                   | set(numpy.arange(FLOOR, NOSE, STOREY).round(6)))
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, STEP)
  rows, faces = [], []
  for k in range(len(heights) - 1):
    z0, z1 = heights[k], heights[k + 1]
    for j in range(len(angles) - 1):
      a0, a1 = angles[j], angles[j + 1]
      if not _inWindow(0.5 * (a0 + a1), 0.5 * (z0 + z1)):
        _cellOf(rows, faces, a0, a1, z0, z1, inner)
  if inner:
    _discOf(rows, faces, NOSE, capsuleRadius(NOSE) - WALL, -1.0)
    return numpy.array(rows), numpy.array(faces, numpy.uint32)
  for (a0, a1), (z0, z1) in WINDOWS:
    middle = (0.5 * (a0 + a1), 0.5 * (z0 + z1))
    for one, two in (((a0, z0), (a1, z0)), ((a1, z0), (a1, z1)),
                     ((a1, z1), (a0, z1)), ((a0, z1), (a0, z0))):
      _jambOf(rows, faces, one, two, middle)
  _coneOf(rows, faces, NOSE, capsuleRadius(NOSE), NOSE + 0.4 * SIZE,
          0.05 * SIZE, True)
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def glassRows() -> tuple:
  """Returns the windows' panes: rows (place, normal) and triangles, in
  the middle of the wall."""
  rows, faces = [], []
  for (a0, a1), (z0, z1) in WINDOWS:
    angles = numpy.arange(a0, a1 + 0.5 * STEP, STEP)
    for j in range(len(angles) - 1):
      first = len(rows)
      for a, z in ((angles[j], z0), (angles[j + 1], z0),
                   (angles[j + 1], z1), (angles[j], z1)):
        r = capsuleRadius(z) - 0.5 * WALL
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        rows.append((r * c, r * s, z, c, s, 0.0))
      faces.extend((first, first + 1, first + 2, first, first + 2,
                    first + 3))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def floorRows() -> tuple:
  """Returns the cabin's floor: a disc over the tank, facing up, its
  boards laid across it ('BOARD_TILE' m a picture)."""
  rows, faces = [], []
  _discOf(rows, faces, FLOOR + 0.001, capsuleRadius(FLOOR) - WALL, 1.0)
  out = numpy.zeros((len(rows), 8))
  out[:, :6] = numpy.array(rows)
  out[:, 6] = out[:, 0] / BOARD_TILE
  out[:, 7] = out[:, 1] / BOARD_TILE
  return out, numpy.array(faces, numpy.uint32)


def innerWall() -> tuple:
  """Returns the capsule's inner wall and ceiling, its pine planks
  running round it ('PINE_TILE' m a picture: round at a fixed radius,
  so the planks keep their width up the cone)."""
  rows, faces = capsuleShell(True)
  out = numpy.zeros((len(rows), 8))
  out[:, :6] = rows
  out[:, 6] = numpy.arctan2(out[:, 1], out[:, 0]) * 4.5 / PINE_TILE
  out[:, 7] = (out[:, 2] - FLOOR) / PINE_TILE
  return out, faces


def seatRows() -> tuple:
  """Returns the office chair's seat and back (user, 2026-11-16: "Asger
  sits in what is more like an office chair"), upholstered."""
  return _joined([_box(middle, half) for middle, half in (CUSHION,
                                                          BACKREST)])


def chairFrame() -> tuple:
  """Returns the office chair's frame: five legs out from its foot on
  castors, its gas column up to the seat, the stem up the back."""
  (x, y, z), half = CUSHION
  under = z - half[2]
  parts = []
  for k in range(5):
    a = 2.0 * math.pi * k / 5.0
    c, s = math.cos(a), math.sin(a)
    axes = ((c, s, 0.0), (-s, c, 0.0), (0.0, 0.0, 1.0))
    parts.append(_box((x + 0.17 * c, y + 0.17 * s, FLOOR + 0.07),
                      (0.17, 0.022, 0.015), axes))
    parts.append(_box((x + 0.33 * c, y + 0.33 * s, FLOOR + 0.025),
                      (0.025, 0.02, 0.025), axes))
  column = 0.5 * (under - FLOOR - 0.07)
  parts.append(_box((x, y, FLOOR + 0.07 + column), (0.025, 0.025,
                                                    column)))
  (bx, by, bz), back = BACKREST
  stem = 0.5 * (bz - back[2] - under)
  parts.append(_box((bx - 0.02, by, under + stem), (0.015, 0.03, stem)))
  return _joined(parts)


def consoleRows() -> tuple:
  """Returns the consoles' rosewood bodies either side of the seat."""
  return _joined([_box(middle, half) for middle, half in (LEFT_CONSOLE,
                                                          RIGHT_CONSOLE)])


def consoleTops() -> tuple:
  """Returns the consoles' brushed aluminium tops: plates on their
  rosewood, their faces at 'TOP' (what lies on a console lies on
  them)."""
  return _joined([_box((m[0], m[1], m[2] + h[2] + 0.002), (h[0] + 0.004,
                                                           h[1] + 0.004,
                                                           0.002))
                  for m, h in (LEFT_CONSOLE, RIGHT_CONSOLE)])


#  A box's faces: the normal in its own axes and its corners (each -1 or
#  1 along right, up, out), seen from outside counter-clockwise.
_BOX_FACES = (
  ((0, 0, 1), ((-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))),
  ((0, 0, -1), ((1, -1, -1), (-1, -1, -1), (-1, 1, -1), (1, 1, -1))),
  ((1, 0, 0), ((1, -1, 1), (1, -1, -1), (1, 1, -1), (1, 1, 1))),
  ((-1, 0, 0), ((-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1))),
  ((0, 1, 0), ((-1, 1, 1), (1, 1, 1), (1, 1, -1), (-1, 1, -1))),
  ((0, -1, 0), ((-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1))))


def _inWindow(angle: float, z: float) -> bool:
  """Returns whether the cone's point at 'angle' (deg) and 'z' is in a
  window."""
  return any(a0 <= angle <= a1 and z0 <= z <= z1
             for (a0, a1), (z0, z1) in WINDOWS)


def _onCone(angle: float, z: float, inner: bool) -> tuple:
  """Returns a row of the cone at 'angle' (deg) and 'z': the skin's or
  the inner wall's, its normal outward or inward."""
  r = capsuleRadius(z) - (WALL if inner else 0.0)
  c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
  slope = (capsuleRadius(FLOOR) - capsuleRadius(NOSE)) / (NOSE - FLOOR)
  size = math.sqrt(1.0 + slope * slope)
  sign = -1.0 if inner else 1.0
  return (r * c, r * s, z, sign * c / size, sign * s / size,
          sign * slope / size)


def _cellOf(rows: list, faces: list, a0: float, a1: float, z0: float,
            z1: float, inner: bool) -> None:
  """Adds a cell of the cone between 'a0' and 'a1' (deg), 'z0' and
  'z1', the skin's or the inner wall's, facing out of its side."""
  first = len(rows)
  for a, z in ((a0, z0), (a1, z0), (a1, z1), (a0, z1)):
    rows.append(_onCone(a, z, inner))
  if inner:
    faces.extend((first, first + 2, first + 1, first, first + 3,
                  first + 2))
  else:
    faces.extend((first, first + 1, first + 2, first, first + 2,
                  first + 3))


def _jambOf(rows: list, faces: list, one: tuple, two: tuple,
            middle: tuple) -> None:
  """Adds a window's jamb along its edge from 'one' to 'two' (angle,
  height): the wall's thickness, closing the cut, facing into the
  window (whose 'middle' it is)."""
  corners = [_onCone(a, z, inner)[:3] for (a, z), inner in (
    (one, False), (two, False), (two, True), (one, True))]
  along = numpy.subtract(corners[1], corners[0])
  through = numpy.subtract(corners[3], corners[0])
  normal = numpy.cross(along, through)
  inward = numpy.subtract(_onCone(*middle, False)[:3], corners[0])
  if numpy.dot(normal, inward) < 0.0:
    normal = -normal
  normal = tuple(normal / numpy.linalg.norm(normal))
  first = len(rows)
  for corner in corners:
    rows.append(tuple(corner) + normal)
  faces.extend((first, first + 1, first + 2, first, first + 2, first + 3))


def _coneOf(rows: list, faces: list, z0: float, r0: float, z1: float,
            r1: float, top: bool) -> None:
  """Adds a frustum from 'z0' (radius 'r0') to 'z1' ('r1'), its top
  closed if asked."""
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, 4 * STEP)
  slope = (r0 - r1) / (z1 - z0)
  size = math.sqrt(1.0 + slope * slope)
  for j in range(len(angles) - 1):
    first = len(rows)
    for a, z, r in ((angles[j], z0, r0), (angles[j + 1], z0, r0),
                    (angles[j + 1], z1, r1), (angles[j], z1, r1)):
      c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
      rows.append((r * c, r * s, z, c / size, s / size, slope / size))
    faces.extend((first, first + 1, first + 2, first, first + 2,
                  first + 3))
  if top:
    _discOf(rows, faces, z1, r1, 1.0)


def _discOf(rows: list, faces: list, z: float, radius: float,
            up: float) -> None:
  """Adds a disc at height 'z', 'radius' m round, facing 'up' (+1) or
  down (-1)."""
  middle = len(rows)
  rows.append((0.0, 0.0, z, 0.0, 0.0, up))
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, 4 * STEP)
  for a in angles:
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    rows.append((radius * c, radius * s, z, 0.0, 0.0, up))
  for j in range(len(angles) - 1):
    one, two = middle + 1 + j, middle + 2 + j
    faces.extend((middle, one, two) if up > 0 else (middle, two, one))


def _box(middle: tuple, half: tuple, axes: tuple = None) -> tuple:
  """Returns a box's rows (place, normal) and triangles: its 'middle',
  'half' sizes along its 'axes' (right, up, out; the vessel's own when
  None)."""
  axes = axes or ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
  rows, faces = [], []
  for normal, corners in _BOX_FACES:
    first = len(rows)
    direction = tuple(normal[0] * a + normal[1] * b + normal[2] * n
                      for a, b, n in zip(*axes))
    for corner in corners:
      place = tuple(m + corner[0] * half[0] * a + corner[1] * half[1] * b
                    + corner[2] * half[2] * n for m, a, b, n in zip(
        middle, *axes))
      rows.append(place + direction)
    faces.extend((first, first + 1, first + 2, first, first + 2,
                  first + 3))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _joined(parts: list) -> tuple:
  """Returns the rows and triangles of 'parts' as one mesh."""
  rows, faces, count = [], [], 0
  for part, indices in parts:
    rows.append(part)
    faces.append(indices + count)
    count += len(part)
  return numpy.concatenate(rows), numpy.concatenate(faces).astype(
    numpy.uint32)
