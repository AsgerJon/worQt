"""
The space station's shape (user, 2026-11-17: "Think 2001: A Space
Odyssey"; "1800m, but also: have some 300m antennas sticking out of the
station that has RGB lighting. Like we are back in the 2015 waiting for
GTA V for PC with corsair or whatever the fuck RGB lol... that will be
fucking visible from the gorund"), Qt-free, in its own axes (z its
axis, the docking port's way; m), each mesh by its look: the ring (a
round tube, its deck inside 'FLOOR_RADIUS' from the axis: round, some
of it is always lit), its hub on
the axis with the docking port at its +z end, four spokes from the hub
to the ring (the elevators' shafts), lit windows along the ring's sides,
the port's collar, five 300 m antennas (one along the axis behind the
hub, four out of the ring between the spokes) and a beacon on each
tip. The antennas and beacons wear a rainbow sliding along them (their
picture's u: three rainbows down an antenna, one colour a beacon).
Rows of eight (place, normal, where on a picture).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._shapes import UNTURNED, ballRows, cylinderRows, joined, quadRows
from ._shapes import ringRows
from ._station import FLOOR_RADIUS

TAU = 2.0 * math.pi
#  The ring: a round tube, its radius and how far its middle is from the
#  axis (its deck, the floor, lies 'FLOOR_RADIUS' out: 8 m over the
#  tube's bottom), m; its segments round the station and round the tube.
TUBE = 22.0
TUBE_MIDDLE = FLOOR_RADIUS - 14.0
HULL = TUBE_MIDDLE + TUBE - FLOOR_RADIUS
SEGMENTS = 256
TUBE_SIDES = 24
#  The hub (radius, length along the axis), the docking port standing
#  out of its +z end (radius, length), its collar (inner, outer radius,
#  m); the spokes (count, radius).
HUB = (40.0, 120.0)
PORT = (8.0, 20.0)
COLLAR = (8.0, 11.5)
SPOKES = (4, 8.0)
#  The windows along the ring's sides: their rows round the tube (rad from
#  the station's axis' way), how far apart round the station (deg), half
#  their size (along, across), m.
WINDOW_ROWS = (math.radians(70.0), math.radians(110.0))
WINDOW_STEP = 1.5
WINDOW_HALF = (2.5, 1.25)
#  The antennas: long, thick (radius), m; how many rainbows run down one;
#  the beacons on their tips (radius, m).
ANTENNA = (300.0, 1.5)
RAINBOWS = 3.0
BEACON = 6.0


def portTip() -> tuple:
  """Returns the docking port's mouth: its middle (its own axes)."""
  return 0.0, 0.0, 0.5 * HUB[1] + PORT[1]


def ringRowsOf() -> tuple:
  """Returns the ring: a round tube round the axis, 'TUBE' its radius,
  its middle 'TUBE_MIDDLE' out."""
  rows, faces = [], []
  for k in range(SEGMENTS + 1):
    a = TAU * k / SEGMENTS
    c, s = math.cos(a), math.sin(a)
    for j in range(TUBE_SIDES + 1):
      b = TAU * j / TUBE_SIDES
      out, up = math.cos(b), math.sin(b)
      normal = (out * c, out * s, up)
      radius = TUBE_MIDDLE + TUBE * out
      rows.append((radius * c, radius * s, TUBE * up) + normal
                  + (0.002, 0.002))
  ring = TUBE_SIDES + 1
  for k in range(SEGMENTS):
    for j in range(TUBE_SIDES):
      p, q = k * ring + j, k * ring + j + 1
      r, t = (k + 1) * ring + j + 1, (k + 1) * ring + j
      faces.extend((p, t, r, p, r, q))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def hubRows() -> tuple:
  """Returns the hub on the axis and the docking port standing out of
  its +z end, and the four spokes out to the ring's ceiling."""
  radius, long = HUB
  parts = [cylinderRows((0.0, 0.0, -0.5 * long), (0.0, 0.0, 1.0), radius,
                        long, 64),
           cylinderRows((0.0, 0.0, 0.5 * long), (0.0, 0.0, 1.0), PORT[0],
                        PORT[1], 32)]
  count, thick = SPOKES
  reach = TUBE_MIDDLE - TUBE - radius
  for k in range(count):
    a = TAU * k / count
    way = (math.cos(a), math.sin(a), 0.0)
    parts.append(cylinderRows(tuple(radius * w for w in way), way, thick,
                              reach + 1.0, 32))
  return joined(parts)


def windowRows() -> tuple:
  """Returns the ring's windows, lit: two rows along each side of the
  tube, a hair off it."""
  parts = []
  count = int(round(360.0 / WINDOW_STEP))
  for row in WINDOW_ROWS:
    for side in (1.0, -1.0):
      b = row if side > 0 else -row
      out, up = math.cos(b), math.sin(b)
      for k in range(count):
        a = TAU * k / count
        c, s = math.cos(a), math.sin(a)
        normal = (out * c, out * s, up)
        across = (-up * c, -up * s, out)
        along = (-s, c, 0.0)
        radius = TUBE_MIDDLE + (TUBE + 0.05) * out
        parts.append(quadRows((radius * c, radius * s, (TUBE + 0.05) * up),
                              (along, across, normal), WINDOW_HALF))
  return joined(parts)


def collarRows() -> tuple:
  """Returns the docking port's collar: a ring round its mouth (it
  glows: where to dock)."""
  x, y, z = portTip()
  return ringRows((x, y, z + 0.1), UNTURNED, COLLAR[0], COLLAR[1], 0.5)


def antennaRows() -> tuple:
  """Returns the antennas: one along the axis behind the hub, four out
  of the ring between the spokes; their picture's u runs 'RAINBOWS'
  times down each."""
  long, radius = ANTENNA
  parts = [_mastRows((0.0, 0.0, -0.5 * HUB[1]), (0.0, 0.0, -1.0), long,
                     radius)]
  out = FLOOR_RADIUS + HULL
  for k in range(SPOKES[0]):
    a = TAU * (k + 0.5) / SPOKES[0]
    way = (math.cos(a), math.sin(a), 0.0)
    parts.append(_mastRows(tuple(out * w for w in way), way, long, radius))
  return joined(parts)


def beaconTips() -> tuple:
  """Returns where the beacons are: on each antenna's tip (its own
  axes)."""
  tips = [(0.0, 0.0, -0.5 * HUB[1] - ANTENNA[0])]
  out = FLOOR_RADIUS + HULL + ANTENNA[0]
  for k in range(SPOKES[0]):
    a = TAU * (k + 0.5) / SPOKES[0]
    tips.append((out * math.cos(a), out * math.sin(a), 0.0))
  return tuple(tips)


def beaconRows() -> tuple:
  """Returns a beacon on each antenna's tip, each one colour of the
  rainbow (its picture's u the same all over, each its own)."""
  tips = beaconTips()
  parts = []
  for k, tip in enumerate(tips):
    rows, faces = ballRows(tip, BEACON, 16)
    rows[:, 6], rows[:, 7] = k / len(tips), 0.5
    parts.append((rows, faces))
  return joined(parts)


@functools.lru_cache(maxsize=1)
def stationMeshes() -> dict:
  """Returns the station's meshes by look: 'hull', 'windows', 'collar',
  'antennas', 'beacons'."""
  return {'hull': joined([ringRowsOf(), hubRows()]),
          'windows': windowRows(), 'collar': collarRows(),
          'antennas': antennaRows(), 'beacons': beaconRows()}


def _mastRows(base: tuple, way: tuple, long: float, radius: float) -> tuple:
  """Returns an antenna's mast from 'base' 'long' along 'way', open at
  its ends; its picture's u from nought at its foot to 'RAINBOWS' at its
  tip, its v round."""
  way = numpy.array(way, numpy.float64)
  other = numpy.array((0.0, 0.0, 1.0)) if abs(way[2]) < 0.9 else (
    numpy.array((1.0, 0.0, 0.0)))
  right = numpy.cross(way, other)
  right /= numpy.linalg.norm(right)
  up = numpy.cross(way, right)
  base = numpy.array(base, numpy.float64)
  sides, rows, faces = 16, [], []
  for k in range(sides + 1):
    a = TAU * k / sides
    round_ = math.cos(a) * right + math.sin(a) * up
    for share in (0.0, 1.0):
      place = base + share * long * way + radius * round_
      rows.append(tuple(place) + tuple(round_) + (RAINBOWS * share,
                                                  k / sides))
  for k in range(sides):
    a, b = 2 * k, 2 * k + 2
    faces.extend((a, b, b + 1, a, b + 1, a + 1))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)
