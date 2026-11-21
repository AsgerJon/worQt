"""
The space station's shape (user, 2026-11-17: "Think 2001: A Space
Odyssey"; "1800m, but also: have some 300m antennas sticking out of the
station that has RGB lighting. Like we are back in the 2015 waiting for
GTA V for PC with corsair or whatever the fuck RGB lol... that will be
fucking visible from the gorund"), Qt-free, in its own axes (z its
axis, the docking's way; m), each mesh by its look: the ring (a round
tube, its deck inside 'FLOOR_RADIUS' from the axis: round, some of it
is always lit), the drum on the axis (user, 2026-11-19: "On Terra Prime
the center room between the spokes is gone. Instead, the head our
rocket insert itself here, so that the spokes align with the doors to
our top floor"): a short round block with a hole through it on the
axis, the socket a rocket's head slides into from either side (user,
2026-11-18: "Terra Prime should have docking ports on both sides"),
four shafts' mouths in its hole's wall; four spokes from the drum to
the ring, open girders the elevators' cages ride down in vacuum (user,
2026-11-19: "the spokes are not pressurized. Only the elevators are
They are large girder structures"), lit windows along the ring's sides,
the socket's collars round the hole at either face, four 300 m
antennas out of the ring between the spokes ("remove the antennas that
are perpendicular to the plane of Terra Prime") and a beacon on each
tip. The antennas and beacons wear a rainbow sliding along them (their
picture's u: three rainbows down an antenna, one colour a beacon).
Rows of eight (place, normal, where on a picture).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from ._levels import DOOR_HALF_HIGH, DOOR_HALF_SPAN, DOORS_HIGH, HEAD
from ._levels import TIP, WALL
from ._shapes import UNTURNED, ballRows, boxRows, joined, quadRows
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
#  The drum (its hole's radius: a rocket's head is '_levels.HEAD' round,
#  half a metre clear all round; its outer radius; half its length along
#  the axis: a docked rocket's head is in it from its level 1 up, its
#  level 0's cone outside), m; the shafts in it and in the spokes (their
#  inside radius: a cage fits, '_elevator'); the spokes (count, radius);
#  the sockets' sides (+z, -z); the collars round the hole (inner, outer
#  radius, m); the sides round of the drum and the hole.
SOCKET = 4.5
DRUM = 12.0
DRUM_HALF = 4.75
SHAFT = 2.7
SPOKES = (4, 4.5)
SIDES = (1.0, -1.0)
COLLAR = (SOCKET + 0.2, SOCKET + 2.0)
SIDES_ROUND = 96
#  The girders: each spoke's four chords this far off its way both ways
#  (the cages ride inside), their half thickness; a frame across them
#  and a diagonal on each face every 'BAY' m, half as thick, m.
GIRDER = 3.0
CHORD = 0.25
BAY = 12.0
#  The spokes' lamps (user, 2026-11-19: "we need illuminated spokes"): a
#  glowing cube on each of a girder's four corners at every frame, this
#  half size (standing out of its chords), m.
SPOKE_LAMP = 0.5
#  The hole's wall's cells along the axis. Each shaft's mouth in it is
#  shut but for an opening as wide and high as a docked rocket's top
#  floor's door (its sleeve's: half its width and height, m; user,
#  2026-11-19: the shafts' mouths were open to the gap round the head,
#  space seen from the cage past the sleeve).
HOLE_CUTS = 24
OPENING = ((HEAD - WALL) * math.sin(math.radians(DOOR_HALF_SPAN)),
           DOOR_HALF_HIGH)
#  The ring's glass (user, 2026-11-19: "In the ring, make the window span
#  the whole way. Right now there are just two narrow stripes of
#  windows"): the tube glazed from this far round it from straight out
#  (rad; either way, over its top: 3.5 m over the deck at its sides), on
#  the hull's own grid (a whole number of its cells round the tube): the
#  hull is left out there and the glass laid in its place, sharing its
#  edges (laid a hair off the hull, the two fought for the depth seen
#  from across the ring, the user, 2026-11-21: "The glass roof on the
#  ring renders with collisions when seen from the outside").
GLAZED = math.radians(60.0)
GLAZED_CELLS = round(GLAZED * TUBE_SIDES / TAU)
if abs(GLAZED_CELLS * TAU / TUBE_SIDES - GLAZED) > 1e-12:
  raise ValueError('the glass must start on the hull\'s grid')
#  The antennas: long, thick (radius), m; how many rainbows run down one;
#  the beacons on their tips (radius, m).
ANTENNA = (300.0, 1.5)
RAINBOWS = 3.0
BEACON = 6.0


def portTip(side: float = 1.0) -> tuple:
  """Returns where a docked rocket's nose's tip is (its own axes), the
  rocket in from +z ('side' one) or -z (minus one): its top floor's
  doors in the station's plane, its nose through it, the tip past it."""
  return 0.0, 0.0, -side * (TIP - DOORS_HIGH)


def ringRowsOf() -> tuple:
  """Returns the ring: a round tube round the axis, 'TUBE' its radius,
  its middle 'TUBE_MIDDLE' out; where it is glazed ('GLAZED') left out
  ('windowRows' lies there)."""
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
      if GLAZED_CELLS <= j < TUBE_SIDES - GLAZED_CELLS:
        continue
      p, q = k * ring + j, k * ring + j + 1
      r, t = (k + 1) * ring + j + 1, (k + 1) * ring + j
      faces.extend((p, t, r, p, r, q))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def drumRows() -> tuple:
  """Returns the drum on the axis: its outer side (each shaft's tunnel's
  way out cut through it), its two faces round the hole, the hole's
  wall (the shafts' mouths shut but for a door-sized opening)."""
  parts = [outerRows()]
  for side in SIDES:
    parts.append(_annulusRows((0.0, 0.0, side * DRUM_HALF),
                              _portAxes(side), SOCKET, DRUM))
  parts.append(holeRows())
  return joined(parts)


def outerRows() -> tuple:
  """Returns the drum's outer side, facing out, a hole cut where each
  shaft's tunnel comes out of it (its cells' middles within the
  tunnel's round)."""
  rows, faces = [], []
  nu, nv = SIDES_ROUND * 2, HOLE_CUTS
  for i in range(nu):
    u0, u1 = TAU * i / nu, TAU * (i + 1) / nu
    for j in range(nv):
      v0 = -DRUM_HALF + 2.0 * DRUM_HALF * j / nv
      v1 = -DRUM_HALF + 2.0 * DRUM_HALF * (j + 1) / nv
      across = DRUM * math.sin(shaftWay(0.5 * (u0 + u1)))
      if math.hypot(across, 0.5 * (v0 + v1)) < SHAFT:
        continue
      first = len(rows)
      for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        c, s = math.cos(u), math.sin(u)
        rows.append((DRUM * c, DRUM * s, v, c, s, 0.0, u / TAU, v))
      faces.extend((first, first + 1, first + 2, first, first + 2,
                    first + 3))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


#  A girder's corners (across its spoke, along the axis: shares of
#  'GIRDER').
CORNERS = ((1.0, 1.0), (-1.0, 1.0), (-1.0, -1.0), (1.0, -1.0))


def _girderSpan() -> tuple:
  """Returns where the girders start and end out from the axis (inside
  the drum, into the ring's tube) and how many bays they have."""
  start = DRUM - 0.5
  end = TUBE_MIDDLE - TUBE + 1.0
  return start, end, int((end - start) / BAY)


def _girderAt(k: int, out: float, corner: tuple) -> tuple:
  """Returns spoke 'k''s girder's corner 'corner' 'out' m from the axis
  (the station's own axes)."""
  a = TAU * k / SPOKES[0]
  way = (math.cos(a), math.sin(a), 0.0)
  side = (-math.sin(a), math.cos(a), 0.0)
  axial = (0.0, 0.0, 1.0)
  return tuple(out * w + GIRDER * corner[0] * s + GIRDER * corner[1] * z
               for w, s, z in zip(way, side, axial))


def spokeLampRows() -> tuple:
  """Returns the spokes' lamps: a cube on each girder's corners at each
  of its frames ('SPOKE_LAMP'), square to its spoke."""
  parts = []
  start, _, bays = _girderSpan()
  for k in range(SPOKES[0]):
    a = TAU * k / SPOKES[0]
    axes = ((math.cos(a), math.sin(a), 0.0),
            (-math.sin(a), math.cos(a), 0.0), (0.0, 0.0, 1.0))
    for b in range(bays + 1):
      for corner in CORNERS:
        parts.append(boxRows(_girderAt(k, start + BAY * b, corner),
                             (SPOKE_LAMP,) * 3, axes))
  return joined(parts)


def girderRows() -> tuple:
  """Returns the four spokes' girders: each four chords from inside the
  drum to into the ring's tube, a frame across them and a diagonal on
  each of its faces every 'BAY' m."""
  parts = []
  start, end, bays = _girderSpan()
  corners = CORNERS
  for k in range(SPOKES[0]):

    def at(out: float, corner: tuple, k: int = k) -> tuple:
      return _girderAt(k, out, corner)

    for corner in corners:
      parts.append(_beamRows(at(start, corner), at(end, corner), CHORD))
    for b in range(bays + 1):
      out = start + BAY * b
      for one, two in zip(corners, corners[1:] + corners[:1]):
        parts.append(_beamRows(at(out, one), at(out, two), 0.5 * CHORD))
        if b < bays:
          parts.append(_beamRows(at(out, one), at(out + BAY, two),
                                 0.5 * CHORD))
  return joined(parts)


def _beamRows(one: tuple, two: tuple, half: float) -> tuple:
  """Returns a square beam from 'one' to 'two', 'half' its half
  thickness."""
  way = numpy.subtract(two, one)
  long = float(numpy.linalg.norm(way))
  way = way / long
  other = (0.0, 0.0, 1.0) if abs(way[2]) < 0.9 else (1.0, 0.0, 0.0)
  right = numpy.cross(way, other)
  right /= numpy.linalg.norm(right)
  up = numpy.cross(way, right)
  middle = tuple(0.5 * (a + b) for a, b in zip(one, two))
  return boxRows(middle, (half, half, 0.5 * long), (tuple(right),
                                                    tuple(up), tuple(way)))


def shaftWay(angle: float) -> float:
  """Returns how far 'angle' (rad round the axis) is from the nearest
  shaft's way, rad (signed: round the axis's way past it)."""
  count = SPOKES[0]
  return min(((angle - TAU * k / count + math.pi) % TAU - math.pi
              for k in range(count)), key=abs)


def holeGrid() -> tuple:
  """Returns the drum's hole's wall's grid: its cells' edges round (rad)
  and along the axis (m), each opening's edges among them."""
  half, high = OPENING
  edge = math.asin(half / SOCKET)
  us = {TAU * i / (2 * SIDES_ROUND) for i in range(2 * SIDES_ROUND + 1)}
  for k in range(SPOKES[0]):
    middle = TAU * k / SPOKES[0]
    us |= {(middle - edge) % TAU, (middle + edge) % TAU}
  vs = {-DRUM_HALF + 2.0 * DRUM_HALF * j / HOLE_CUTS
        for j in range(HOLE_CUTS + 1)} | {-high, high}
  return sorted(us), sorted(vs)


def inOpening(u: float, v: float) -> bool:
  """Returns whether the hole's wall's point 'u' rad round, 'v' m along
  the axis is in a shaft's mouth's opening."""
  return (abs(SOCKET * math.sin(shaftWay(u))) < OPENING[0]
          and abs(v) < OPENING[1])


def holeRows() -> tuple:
  """Returns the drum's hole's wall, facing the axis (a rocket's head
  slides in along it), each shaft's mouth's opening cut in it."""
  us, vs = holeGrid()
  rows, faces = [], []
  for u0, u1 in zip(us[:-1], us[1:]):
    for v0, v1 in zip(vs[:-1], vs[1:]):
      if inOpening(0.5 * (u0 + u1), 0.5 * (v0 + v1)):
        continue
      first = len(rows)
      for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        c, s = math.cos(u), math.sin(u)
        rows.append((SOCKET * c, SOCKET * s, v, -c, -s, 0.0, u / TAU,
                     v))
      faces.extend((first, first + 2, first + 1, first, first + 3,
                    first + 2))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def windowRows() -> tuple:
  """Returns the ring's glass as it is seen from outside, lit: a band
  round the station over the tube's top from 'GLAZED' round it either
  way, in the hull's place on its grid ('ringRowsOf'), facing out."""
  radius = TUBE
  nu, nv = SEGMENTS, TUBE_SIDES - 2 * GLAZED_CELLS
  rows, faces = [], []
  for i in range(nu + 1):
    a = TAU * i / nu
    c, s = math.cos(a), math.sin(a)
    for j in range(nv + 1):
      b = GLAZED + (TAU - 2.0 * GLAZED) * j / nv
      out, up = math.cos(b), math.sin(b)
      far = TUBE_MIDDLE + radius * out
      rows.append((far * c, far * s, radius * up, out * c, out * s, up,
                   i / nu, j / nv))
  for i in range(nu):
    for j in range(nv):
      a, b = i * (nv + 1) + j, (i + 1) * (nv + 1) + j
      faces.extend((a, b + 1, a + 1, a, b, b + 1))
  return numpy.array(rows, numpy.float64), numpy.array(faces, numpy.uint32)


def collarRows() -> tuple:
  """Returns the sockets' collars: a ring round the hole at each of the
  drum's faces (they glow: where to dock)."""
  parts = []
  for side in SIDES:
    right, up, out = UNTURNED
    axes = (right, tuple(side * u for u in up), tuple(side * o for o in out))
    parts.append(ringRows((0.0, 0.0, side * (DRUM_HALF + 0.1)), axes,
                          COLLAR[0], COLLAR[1], 0.5))
  return joined(parts)


def antennaRows() -> tuple:
  """Returns the antennas: four out of the ring between the spokes;
  their picture's u runs 'RAINBOWS' times down each."""
  long, radius = ANTENNA
  parts = []
  out = FLOOR_RADIUS + HULL
  for k in range(SPOKES[0]):
    a = TAU * (k + 0.5) / SPOKES[0]
    way = (math.cos(a), math.sin(a), 0.0)
    parts.append(_mastRows(tuple(out * w for w in way), way, long, radius))
  return joined(parts)


def beaconTips() -> tuple:
  """Returns where the beacons are: on each antenna's tip (its own
  axes)."""
  tips = []
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


def stationMeshes() -> dict:
  """Returns the station's meshes by look: 'hull', 'girders', 'spoke
  lamps', 'windows', 'collar', 'antennas', 'beacons'."""
  return {'hull': joined([ringRowsOf(), drumRows()]),
          'girders': girderRows(), 'spoke lamps': spokeLampRows(),
          'windows': windowRows(),
          'collar': collarRows(), 'antennas': antennaRows(),
          'beacons': beaconRows()}


def _annulusRows(middle: tuple, axes: tuple, inner: float,
                 outer: float) -> tuple:
  """Returns a flat ring facing out of its 'axes' from 'inner' to
  'outer' round, 'SIDES_ROUND' a turn."""
  right, up, out = axes
  rows, faces = [], []
  for k in range(SIDES_ROUND + 1):
    a = TAU * k / SIDES_ROUND
    way = tuple(math.cos(a) * r + math.sin(a) * u for r, u in zip(right,
                                                                  up))
    for radius in (inner, outer):
      rows.append(tuple(m + radius * w for m, w in zip(middle, way))
                  + tuple(out) + (0.002, 0.002))
  for k in range(SIDES_ROUND):
    a, b = 2 * k, 2 * k + 2
    faces.extend((a, a + 1, b + 1, a, b + 1, b))
  return numpy.array(rows), numpy.array(faces, numpy.uint32)


def _portAxes(side: float) -> tuple:
  """Returns the axes of the drum's face on 'side': right, up, out (out
  of the station along its axis)."""
  return (1.0, 0.0, 0.0), (0.0, side, 0.0), (0.0, 0.0, side)


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
