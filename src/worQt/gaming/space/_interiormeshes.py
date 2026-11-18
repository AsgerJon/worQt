"""
The space station's inside as it is drawn (user, 2026-11-17: "all aboard
Asger's kolonihave i rummet!"), its own axes, every face into the rooms
(seen from inside; the hull's faces outward, culled from in here): the
hub's wall with the shafts' mouths cut, its ends (a port's mouth cut in
each: user, 2026-11-18, "Terra Prime should have docking ports on both
sides"), the ports' tubes and their docking rings; the cages' back
walls through the hub; the four shafts out to the ring; the ring's tube
over its deck, the shafts' holes and four strips of windows along it
cut (the stars and Terra wheel past, once a minute); the deck. Rows of
eight (place, normal, picture u v; the deck's picture in metres along
and across it). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._elevator import backWalls
from ._stationinterior import DECK, HATCH, HUB_INSIDE, PORT_INSIDE
from ._stationinterior import SHAFT_INSIDE, TUBE_INSIDE
from ._stationmeshes import HUB, SPOKES, TUBE_MIDDLE, WINDOW_ROWS, portTip
from ._shapes import boxRows, joined

TAU = 2.0 * math.pi
#  How finely each is cut: round the hub and along it; round a shaft and
#  along it; round the station (the ring and the deck) and round the
#  tube; across the deck.
HUB_CUTS = (192, 48)
SHAFT_CUTS = (16, 48)
RING_CUTS = (720, 28)
DECK_CUTS = 8
#  The window strips round the tube: within this of each window row,
#  rad. A shaft's mouth is cut where a cell's middle is this far inside
#  its round (a little less than round: no gap to space at its corners),
#  m.
STRIP = math.radians(5.0)
MOUTH_INSIDE = 1.2
#  The deck meets the tube's wall this far round from straight out
#  (cos: the deck's distance out over the tube's middle, by its radius).
DECK_ANGLE = math.acos((DECK - TUBE_MIDDLE) / TUBE_INSIDE)
DECK_HALF = TUBE_INSIDE * math.sin(DECK_ANGLE)
#  The hub's ends inside (its z) and how far the shafts reach in the
#  ring (to its deck).
HUB_END = 0.5 * HUB[1] - 1.0


@functools.lru_cache(maxsize=1)
def interiorMeshes() -> dict:
  """Returns the station's inside by look: 'inside' (its walls), 'deck'
  (the ring's floor)."""
  return {'inside': joined([hubRows(), portRows(), shaftRows(),
                            backRows(), ringInsideRows()]),
          'deck': deckRows()}


def gridRows(at: object, us: tuple, vs: tuple, cuts: tuple,
             skip: object = None) -> tuple:
  """Returns a surface cut into a grid: 'at(u, v)' its place and normal
  (into the room), 'u' from 'us[0]' to 'us[1]' and 'v' from 'vs[0]' to
  'vs[1]' in 'cuts' steps each; a cell whose middle 'skip(u, v)' says is
  left out (a hole); the picture's u and v the grid's."""
  nu, nv = cuts
  rows, faces = [], []
  for i in range(nu):
    for j in range(nv):
      u0 = us[0] + (us[1] - us[0]) * i / nu
      u1 = us[0] + (us[1] - us[0]) * (i + 1) / nu
      v0 = vs[0] + (vs[1] - vs[0]) * j / nv
      v1 = vs[0] + (vs[1] - vs[0]) * (j + 1) / nv
      if skip is not None and skip(0.5 * (u0 + u1), 0.5 * (v0 + v1)):
        continue
      first = len(rows)
      for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        place, normal = at(u, v)
        rows.append(tuple(place) + tuple(normal) + (u, v))
      a, b, c, d = first, first + 1, first + 2, first + 3
      p, q, r, w = (rows[k][:3] for k in (a, b, c, d))
      n = rows[c][3:6]
      e = (r[0] - p[0], r[1] - p[1], r[2] - p[2])
      f = (w[0] - q[0], w[1] - q[1], w[2] - q[2])
      facing = ((e[1] * f[2] - e[2] * f[1]) * n[0]
                + (e[2] * f[0] - e[0] * f[2]) * n[1]
                + (e[0] * f[1] - e[1] * f[0]) * n[2])
      if facing >= 0.0:
        faces.extend((a, b, c, a, c, d))
      else:
        faces.extend((a, c, b, a, d, c))
  return numpy.array(rows, numpy.float64), numpy.array(faces, numpy.uint32)


def _spokeAngles() -> tuple:
  """Returns the spokes' angles round the station, rad."""
  count = SPOKES[0]
  return tuple(TAU * k / count for k in range(count))


def _offSpoke(angle: float) -> float:
  """Returns how far 'angle' is round from the nearest spoke, rad."""
  return min(abs((angle - a + math.pi) % TAU - math.pi)
             for a in _spokeAngles())


def hubRows() -> tuple:
  """Returns the hub's wall (the shafts' mouths cut) and its two ends
  (a port's mouth cut in each)."""
  def wall(u: float, v: float) -> tuple:
    c, s = math.cos(u), math.sin(u)
    return (HUB_INSIDE * c, HUB_INSIDE * s, v), (-c, -s, 0.0)

  def mouth(u: float, v: float) -> bool:
    across = HUB_INSIDE * math.sin(_offSpoke(u))
    return math.hypot(across, v) < SHAFT_INSIDE - MOUTH_INSIDE

  parts = [gridRows(wall, (0.0, TAU), (-HUB_END, HUB_END), HUB_CUTS,
                    mouth)]
  for end in (1.0, -1.0):
    low = PORT_INSIDE

    def cap(u: float, v: float, end: float = end) -> tuple:
      return (v * math.cos(u), v * math.sin(u), end * HUB_END), (
        0.0, 0.0, -end)

    parts.append(gridRows(cap, (0.0, TAU), (low, HUB_INSIDE), (96, 6)))
  return joined(parts)


def backRows() -> tuple:
  """Returns the cages' back walls through the hub ('_elevator.
  backWalls': the station turns about its own z), each a box."""
  ways = tuple((math.cos(angle), math.sin(angle), 0.0)
               for angle in _spokeAngles())
  return joined([boxRows(place, half, axes) for place, half, axes in
                 backWalls(ways, (0.0, 0.0, 1.0), (0.0, 0.0, 0.0))])


def portRows() -> tuple:
  """Returns each port's tube from the hub to its mouth and the docking
  ring round the hatch at its mouth."""
  parts = []
  for side in (1.0, -1.0):
    mouth = side * portTip(side)[2]

    def wall(u: float, v: float, side: float = side) -> tuple:
      c, s = math.cos(u), math.sin(u)
      return (PORT_INSIDE * c, PORT_INSIDE * s, side * v), (-c, -s, 0.0)

    def ring(u: float, v: float, side: float = side,
             mouth: float = mouth) -> tuple:
      return (v * math.cos(u), v * math.sin(u), side * (mouth - 0.05)), (
        0.0, 0.0, -side)

    parts += [gridRows(wall, (0.0, TAU), (HUB_END, mouth), (32, 4)),
              gridRows(ring, (0.0, TAU), (HATCH, PORT_INSIDE), (32, 2))]
  return joined(parts)


def shaftRows() -> tuple:
  """Returns the four shafts' tubes from the hub's wall to the ring's
  tube."""
  parts = []
  top = TUBE_MIDDLE - TUBE_INSIDE + 2.0
  for angle in _spokeAngles():
    way = (math.cos(angle), math.sin(angle), 0.0)
    side = (-math.sin(angle), math.cos(angle), 0.0)

    def wall(u: float, v: float, way: tuple = way,
             side: tuple = side) -> tuple:
      round_ = tuple(math.cos(u) * s + math.sin(u) * z for s, z in zip(
        side, (0.0, 0.0, 1.0)))
      place = tuple(v * w + SHAFT_INSIDE * r for w, r in zip(way, round_))
      return place, tuple(-r for r in round_)

    parts.append(gridRows(wall, (0.0, TAU), (HUB_INSIDE - 1.0, top),
                          SHAFT_CUTS))
  return joined(parts)


def ringInsideRows() -> tuple:
  """Returns the ring's tube inside over its deck: the shafts' holes and
  the window strips cut."""
  strips = [r for r in WINDOW_ROWS] + [-r for r in WINDOW_ROWS]

  def wall(u: float, v: float) -> tuple:
    c, s = math.cos(u), math.sin(u)
    out = TUBE_MIDDLE + TUBE_INSIDE * math.cos(v)
    up = TUBE_INSIDE * math.sin(v)
    return (out * c, out * s, up), (-math.cos(v) * c, -math.cos(v) * s,
                                    -math.sin(v))

  def skip(u: float, v: float) -> bool:
    out = TUBE_MIDDLE + TUBE_INSIDE * math.cos(v)
    across = out * math.sin(_offSpoke(u))
    if (math.cos(v) < 0.0 and math.hypot(across, TUBE_INSIDE * math.sin(
        v)) < SHAFT_INSIDE - MOUTH_INSIDE):
      return True
    return any(abs((v - row + math.pi) % TAU - math.pi) < STRIP
               for row in strips)

  return gridRows(wall, (0.0, TAU), (DECK_ANGLE, TAU - DECK_ANGLE),
                  RING_CUTS, skip)


def deckRows() -> tuple:
  """Returns the ring's deck: its floor all round, its picture in metres
  along it and across it."""

  def floor(u: float, v: float) -> tuple:
    angle = u / DECK
    c, s = math.cos(angle), math.sin(angle)
    return (DECK * c, DECK * s, v), (-c, -s, 0.0)

  return gridRows(floor, (0.0, TAU * DECK), (-DECK_HALF, DECK_HALF),
                  (RING_CUTS[0], DECK_CUTS))
