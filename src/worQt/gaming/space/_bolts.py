"""
The magic bolts (user, 2026-11-17: "Let the space station and the rocket
have a few clearly marked 'magic' bolts in the walls floors and
ceilings. The gravity gun can pull Asger towards them"), Qt-free, the
vessel's own axes: where each sits in the rocket's cabin and which way
it faces (into the room), and how it is drawn: a steel plate and a bolt
head, a ring round it glowing violet and the enchantment's glint over
it (violet glinting is how magic is marked: the warp knob's). The gun
pulls Asger to 'HOLD' m before a bolt and holds him there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._cockpit import FLOOR, NOSE, WALL, capsuleRadius, seated
from ._shapes import cylinderRows, discRows, joined, ringRows

#  The rocket's bolts: on the floor (x, y), on the ceiling (x, y), on the
#  wall (deg round from x toward y, m over the floor): a few everywhere,
#  clear of the furniture, the windows, the fairy lights and the hatch in
#  the ceiling's middle (going aboard the station); one on the floor
#  right behind his seat ('SEAT_BOLT', a little behind where he stands
#  up: user, 2026-11-17: "put a bolt near or on the seat so I can more
#  easily get back to it": held there, E sits him).
SEAT_BOLT = seated(-0.95, 0.0, 0.0)[:2]
FLOOR_BOLTS = ((0.0, 0.0), (2.2, -0.6), (-1.6, -1.2), (-1.4, 1.6),
               SEAT_BOLT)
CEILING_BOLTS = ((-0.2, 1.2), (1.0, 0.4), (-0.7, -0.8))
WALL_BOLTS = ((0.0, 3.0), (72.0, 3.0), (144.0, 3.0), (-144.0, 3.0),
              (-72.0, 3.0), (36.0, 6.5), (180.0, 6.5), (-108.0, 6.5))
#  A bolt: its plate's radius, its head's radius and height, its ring's
#  inner and outer radius, m; how far before it the gun holds Asger's
#  middle, m (on the floor he stands on it, under the ceiling he hangs
#  from it).
PLATE = 0.08
#  The station's bolts ('stationBolts'): how far up the port's wall from
#  the rocket's nose, how far out on the hub's end wall from its axis,
#  how far short of the shafts' mouths along the hub's wall, m; how many
#  (two, four, four, four); how much bigger than the rocket's they are
#  drawn (seen across the hub).
PORT_ALONG = 4.0
HUB_END = 20.0
HUB_SHORT = 30.0
STATION_BOLTS = 14
STATION_SIZE = 4.0
HEAD = (0.035, 0.025)
RING = (0.095, 0.125)
HOLD = 0.95


@functools.lru_cache(maxsize=1)
def rocketBolts() -> tuple:
  """Returns the rocket's bolts: each its place (on the floor, the
  ceiling or the wall) and the way it faces (a unit vector into the
  room)."""
  out = [((x, y, FLOOR), (0.0, 0.0, 1.0)) for x, y in FLOOR_BOLTS]
  out += [((x, y, NOSE), (0.0, 0.0, -1.0)) for x, y in CEILING_BOLTS]
  slope = (capsuleRadius(NOSE) - capsuleRadius(FLOOR)) / (NOSE - FLOOR)
  lean = 1.0 / math.sqrt(1.0 + slope * slope)
  for angle, high in WALL_BOLTS:
    a = math.radians(angle)
    z = FLOOR + high
    radius = capsuleRadius(z) - WALL
    c, s = math.cos(a), math.sin(a)
    out.append(((radius * c, radius * s, z), (-c * lean, -s * lean,
                                              slope * lean)))
  return tuple(out)


def stationBolts(ways: tuple, floors: tuple) -> tuple:
  """Returns the space station's bolts, docked (user, 2026-11-17: "12
  use bolts to enter Terra Prime docking"), in the docked rocket's own
  axes ('ways': its shafts' ways out; 'floors': its elevators' cages'
  floors from the axis): two on the docking port's wall a little past
  the hatch, four on the hub's end wall round the port's mouth, four on
  the hub's wall short of the shafts' mouths, one on each cage's floor
  (the gun pulls him into the cage): each in the gun's reach of one
  before it; each its place and the way it faces."""
  from ._stationinterior import HUB_INSIDE, HUB_LOW, PLANE, PORT_INSIDE
  from ._stationinterior import PORT_LOW
  out = []
  for way in (ways[0], ways[2]):
    out.append(((PORT_INSIDE * way[0], PORT_INSIDE * way[1],
                 PORT_LOW + PORT_ALONG), tuple(-w for w in way)))
  for way in ways:
    out.append(((HUB_END * way[0], HUB_END * way[1], HUB_LOW),
                (0.0, 0.0, 1.0)))
  for way in ways:
    out.append(((HUB_INSIDE * way[0], HUB_INSIDE * way[1],
                 PLANE - HUB_SHORT), tuple(-w for w in way)))
  for way, floor in zip(ways, floors):
    out.append(((floor * way[0], floor * way[1], PLANE),
                tuple(-w for w in way)))
  return tuple(out)


def holdOf(bolt: tuple) -> tuple:
  """Returns where the gun holds Asger's middle at 'bolt'."""
  place, way = bolt
  return tuple(p + HOLD * w for p, w in zip(place, way))


def axesOf(way: tuple) -> tuple:
  """Returns a bolt's axes facing 'way': right, up, out (right-handed)."""
  other = (0.0, 0.0, 1.0) if abs(way[2]) < 0.9 else (1.0, 0.0, 0.0)
  right = (other[1] * way[2] - other[2] * way[1],
           other[2] * way[0] - other[0] * way[2],
           other[0] * way[1] - other[1] * way[0])
  size = math.sqrt(sum(x * x for x in right))
  right = tuple(x / size for x in right)
  up = (way[1] * right[2] - way[2] * right[1],
        way[2] * right[0] - way[0] * right[2],
        way[0] * right[1] - way[1] * right[0])
  return right, up, tuple(way)


def boltRows() -> tuple:
  """Returns the bolts' steel: each a plate a hair off its surface and
  a six-sided head standing out of it."""
  parts = []
  for place, way in rocketBolts():
    axes = axesOf(way)
    lifted = tuple(p + 0.003 * w for p, w in zip(place, way))
    parts.append(discRows(lifted, axes, PLATE, 24, None))
    parts.append(cylinderRows(lifted, way, HEAD[0], HEAD[1], 6))
  return joined(parts)


def boltRingRows() -> tuple:
  """Returns the bolts' rings: each a flat ring round its plate (they
  glow violet: magic)."""
  parts = []
  for place, way in rocketBolts():
    lifted = tuple(p + 0.002 * w for p, w in zip(place, way))
    parts.append(ringRows(lifted, axesOf(way), RING[0], RING[1], 0.003))
  return joined(parts)


def boltGlintRows() -> tuple:
  """Returns the bolts' glint: a disc over each ring and plate, the
  glint's picture across it (its streaks slide over)."""
  parts = []
  for place, way in rocketBolts():
    lifted = tuple(p + (HEAD[1] + 0.002) * w for p, w in zip(place, way))
    parts.append(discRows(lifted, axesOf(way), RING[1], 32,
                          (0.0, 0.0, 1.0, 1.0)))
  return joined(parts)


def boltPieceRows() -> tuple:
  """Returns one of the station's bolts' steel about its place, facing
  up: a plate and a six-sided head ('STATION_SIZE' times the rocket's;
  placed each frame)."""
  axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
  big = STATION_SIZE
  lifted = (0.0, 0.0, 0.003 * big)
  return joined([discRows(lifted, axes, big * PLATE, 24, None),
                 cylinderRows(lifted, (0.0, 0.0, 1.0), big * HEAD[0],
                              big * HEAD[1], 6)])


def ringPieceRows() -> tuple:
  """Returns one of the station's bolts' glowing ring about its place,
  facing up."""
  axes = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
  big = STATION_SIZE
  return ringRows((0.0, 0.0, 0.002 * big), axes, big * RING[0],
                  big * RING[1], 0.003 * big)
