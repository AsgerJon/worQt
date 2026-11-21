"""
The cabin's meshes, in the vessel's own axes ('_cockpit' has where
everything is; '_levels' the capsule's three levels): the capsule's
skin (its cone, its head and its nose) and its inner wall up its three
levels with the windows, the door and the top floor's four doors cut
through both (from outside you see Asger through the glass), the glass,
the floors and the ceilings (a hatch through each slab), the seat, the
consoles' rosewood and their aluminium tops. The dashboard on them is
'_dashboard''s. Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._cockpit import BACKREST, CUSHION, FLOOR, LEFT_CONSOLE
from ._cockpit import RIGHT_CONSOLE, WALL, WINDOWS, capsuleRadius
from ._cabinpictures import BOARD_TILE, PINE_TILE
from ._levels import HATCH, LEVELS, ROOF, TIP, TIP_RADIUS, TOP_DOORS
from ._levels import hullSlope
from ._walkway import DOOR

#  The hull's round in steps of this many degrees (the windows' and the
#  doors' edges fall on them), its heights at least every 'STOREY' m and
#  at every window's and door's edge. The openings cut through the
#  walls: the windows, the door ('_walkway.DOOR', round 180 deg: its
#  span past 180) and the top floor's four ('_levels.TOP_DOORS').
STEP = 2.0
STOREY = 0.2
#  The pilot's seat: its bolsters' half sizes (along, across, up), its
#  headrest's, its pedestal's (along, across), m.
BOLSTER = (0.25, 0.04, 0.07)
HEADREST = (0.04, 0.12, 0.1)
PEDESTAL = (0.12, 0.16)
OPENINGS = WINDOWS + (DOOR,) + TOP_DOORS


def capsuleShell(inner: bool) -> tuple:
  """Returns the capsule's skin (its cone and head, the openings' jambs
  through the wall, its nose) or, 'inner', its inner wall up each level
  (and the ceilings, the hatches through the slabs), the openings cut
  through both: rows (place, normal) and triangles."""
  spans = LEVELS if inner else ((FLOOR, ROOF),)
  edges = {z for _, span in OPENINGS for z in span}
  rows, faces = [], []
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, STEP)
  for low, high in spans:
    heights = sorted({low, high} | {z for z in edges if low < z < high}
                     | {z for z in (LEVELS[0][1], ROOF) if low < z < high}
                     | set(numpy.arange(low, high, STOREY).round(6)))
    for k in range(len(heights) - 1):
      z0, z1 = heights[k], heights[k + 1]
      for j in range(len(angles) - 1):
        a0, a1 = angles[j], angles[j + 1]
        if not _inWindow(0.5 * (a0 + a1), 0.5 * (z0 + z1)):
          _cellOf(rows, faces, a0, a1, z0, z1, inner)
  if inner:
    for k, (low, high) in enumerate(LEVELS):
      wall = capsuleRadius(high) - WALL
      if k < len(LEVELS) - 1:
        _annulusOf(rows, faces, high, HATCH, wall)
        _tunnelOf(rows, faces, high, LEVELS[k + 1][0], HATCH)
      else:
        _discOf(rows, faces, high, wall, -1.0)
    return numpy.array(rows), numpy.array(faces, numpy.uint32)
  for (a0, a1), (z0, z1) in OPENINGS:
    middle = (0.5 * (a0 + a1), 0.5 * (z0 + z1))
    steps = numpy.arange(a0, a1 + 0.5 * STEP, STEP)
    for b0, b1 in zip(steps[:-1], steps[1:]):
      _jambOf(rows, faces, (b0, z0), (b1, z0), middle)
      _jambOf(rows, faces, (b1, z1), (b0, z1), middle)
    for one, two in (((a1, z0), (a1, z1)), ((a0, z1), (a0, z0))):
      _jambOf(rows, faces, one, two, middle)
  _coneOf(rows, faces, ROOF, capsuleRadius(ROOF), TIP, TIP_RADIUS, True)
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
  """Returns the levels' floors: level 0's a disc over the tank, the
  others' rings round their hatches, facing up, their boards laid across
  them ('BOARD_TILE' m a picture)."""
  rows, faces = [], []
  _discOf(rows, faces, FLOOR + 0.001, capsuleRadius(FLOOR) - WALL, 1.0)
  for low, _ in LEVELS[1:]:
    _annulusOf(rows, faces, low + 0.001, HATCH, capsuleRadius(low) - WALL,
               1.0)
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
  """Returns the pilot's seat's upholstery (user, 2026-11-16: "Asger
  sits in what is more like an office chair"; 2026-11-17: "Less office
  chair, more pilot seat"): the seat and the back ('CUSHION',
  'BACKREST'), the bolsters either side of the seat, the headrest."""
  (x, y, z), half = CUSHION
  (bx, by, bz), back = BACKREST
  top = z + half[2]
  parts = [_box(middle, size) for middle, size in (CUSHION, BACKREST)]
  for side in (-1.0, 1.0):
    parts.append(_box((x, y + side * (half[1] + BOLSTER[1]), top),
                      (half[0], BOLSTER[1], BOLSTER[2])))
  parts.append(_box((bx + 0.01, by, bz + back[2] + HEADREST[2] + 0.04),
                    HEADREST))
  return _joined(parts)


def seatShell() -> tuple:
  """Returns the pilot's seat's dark shell: the bucket under the seat,
  the high back behind the backrest and its wings either side."""
  (x, y, z), half = CUSHION
  (bx, by, bz), back = BACKREST
  under = z - half[2]
  high = back[2] + 2.0 * HEADREST[2] + 0.06
  parts = [_box((x, y, under - 0.05), (half[0] + 0.02, half[1] + 0.06,
                                       0.05)),
           _box((bx - back[0] - 0.03, by, bz - back[2] + high), (
             0.03, half[1] + 0.06, high))]
  for side in (-1.0, 1.0):
    parts.append(_box((bx + 0.03, by + side * (back[1] + 0.03), bz), (
      0.07, 0.03, back[2])))
  return _joined(parts)


def harnessRows() -> tuple:
  """Returns the four point harness: the shoulder straps down the
  backrest, the lap straps along the seat, the buckle's plate."""
  (x, y, z), half = CUSHION
  (bx, by, bz), back = BACKREST
  top = z + half[2]
  parts = []
  for side in (-1.0, 1.0):
    parts.append(_box((bx + back[0] + 0.004, by + side * 0.09, bz),
                      (0.004, 0.024, back[2])))
    parts.append(_box((x, y + side * 0.2, top + 0.004), (half[0] - 0.02,
                                                         0.024, 0.004)))
  parts.append(_box((x + half[0] - 0.06, y, top + 0.006), (0.03, 0.04,
                                                           0.006)))
  return _joined(parts)


def chairFrame() -> tuple:
  """Returns the pilot's seat's mount: a pedestal under the bucket,
  bolted to two rails along the floor."""
  (x, y, z), half = CUSHION
  under = z - half[2] - 0.1
  stand = 0.5 * (under - FLOOR)
  parts = [_box((x, y, FLOOR + stand), (PEDESTAL[0], PEDESTAL[1],
                                        stand))]
  for side in (-1.0, 1.0):
    parts.append(_box((x, y + side * 0.18, FLOOR + 0.012), (0.38, 0.025,
                                                            0.012)))
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
  """Returns whether the cone's point at 'angle' (deg) and 'z' is in an
  opening (a window or the door; an opening's span may run past 180)."""
  return any((a0 <= angle <= a1 or a0 <= angle + 360.0 <= a1)
             and z0 <= z <= z1 for (a0, a1), (z0, z1) in OPENINGS)


def _onCone(angle: float, z: float, inner: bool, slope: float = None
            ) -> tuple:
  """Returns a row of the hull at 'angle' (deg) and 'z': the skin's or
  the inner wall's, its normal outward or inward (leant as the hull
  narrows there, 'slope' m a m: None, at 'z')."""
  r = capsuleRadius(z) - (WALL if inner else 0.0)
  c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
  if slope is None:
    slope = hullSlope(z)
  size = math.sqrt(1.0 + slope * slope)
  sign = -1.0 if inner else 1.0
  return (r * c, r * s, z, sign * c / size, sign * s / size,
          sign * slope / size)


def _cellOf(rows: list, faces: list, a0: float, a1: float, z0: float,
            z1: float, inner: bool) -> None:
  """Adds a cell of the cone between 'a0' and 'a1' (deg), 'z0' and
  'z1', the skin's or the inner wall's, facing out of its side."""
  first = len(rows)
  slope = hullSlope(0.5 * (z0 + z1))
  for a, z in ((a0, z0), (a1, z0), (a1, z1), (a0, z1)):
    rows.append(_onCone(a, z, inner, slope))
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


def _annulusOf(rows: list, faces: list, z: float, inner: float,
               outer: float, up: float = -1.0) -> None:
  """Adds a ceiling at height 'z' from 'inner' (the hatch's hole through
  the slab over it) to 'outer' m round, facing down (or a floor round
  the hatch, 'up' one)."""
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, 4 * STEP)
  first = len(rows)
  for a in angles:
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    rows.append((inner * c, inner * s, z, 0.0, 0.0, up))
    rows.append((outer * c, outer * s, z, 0.0, 0.0, up))
  for j in range(len(angles) - 1):
    a, b = first + 2 * j, first + 2 * j + 2
    faces.extend((a, b, b + 1, a, b + 1, a + 1) if up < 0.0 else (
      a, b + 1, b, a, a + 1, b + 1))


def _tunnelOf(rows: list, faces: list, low: float, high: float,
              radius: float) -> None:
  """Adds a hatch's tunnel up through a slab from 'low' to 'high',
  'radius' m round, facing in."""
  angles = numpy.arange(-180.0, 180.0 + 0.5 * STEP, 4 * STEP)
  first = len(rows)
  for a in angles:
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
    rows.append((radius * c, radius * s, low, -c, -s, 0.0))
    rows.append((radius * c, radius * s, high, -c, -s, 0.0))
  for j in range(len(angles) - 1):
    a, b = first + 2 * j, first + 2 * j + 2
    faces.extend((a, b + 1, b, a, a + 1, b + 1))


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
