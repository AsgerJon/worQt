"""
The space station's inside as it is drawn (user, 2026-11-17: "all aboard
Asger's kolonihave i rummet!"), its own axes, every face into the rooms
(seen from inside; the hull's faces outward, culled from in here): the
four shafts' tunnels through the drum (each from the hole's wall, where
a docked rocket's top floor's door opens, to the drum's outer side,
where the spoke's open girders go on: user, 2026-11-19, "the spokes
are not pressurized"), each shut at its root by a bulkhead on the hole's
wall but for its door-sized opening, the sleeves over the gap from a
docked rocket's doors to those openings; the ring's tube over its deck,
a square hole in its ceiling over each terminal's guide tube
('_terminal'), glazed from 3.5 m over the deck at each side over its
top (user, 2026-11-19: "In the ring, make the window span the whole
way": the stars, Terra and the spokes wheel past, once a minute) on a
frame ('frameRows'); the deck. Rows of eight
(place, normal, picture u v; the deck's picture in metres along and
across it). Qt-free.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

import numpy

from ._levels import HEAD
from ._stationinterior import DECK, DOORWAY_HALF, SHAFT_INSIDE
from ._stationinterior import TUBE_INSIDE
from ._stationmeshes import DRUM, SHAFT, SOCKET, SPOKES, TUBE_MIDDLE
from ._stationmeshes import GLAZED, holeGrid, inOpening, shaftWay
from ._terminal import GUIDE_HALF, GUIDE_WALL
from ._shapes import joined

TAU = 2.0 * math.pi
#  How finely each is cut: round a shaft and along it; round the
#  station (the ring and the deck) and round the tube; across the deck.
SHAFT_CUTS = (32, 48)
RING_CUTS = (720, 28)
DECK_CUTS = 8
#  Over each terminal the ceiling's cells are made anew this much finer
#  (round the station, round the tube), its guide tube's square hole cut
#  ('_terminal.GUIDE_HALF' and its walls).
PATCH_CUTS = (24, 24)
#  The glass's frame: a rib round the tube every 'RIB_EVERY' rad round
#  the station, a mullion along the ring at each of 'MULLIONS' (rad round
#  the tube), each this half wide, m.
RIB_EVERY = math.radians(1.0)
MULLIONS = tuple(math.radians(a) for a in (90.0, 120.0, 150.0, 180.0,
                                           210.0, 240.0, 270.0))
FRAME_HALF = 0.25
FRAME_IN = 0.01
HOLE_HALF = GUIDE_HALF + 2.0 * GUIDE_WALL
#  The deck meets the tube's wall this far round from straight out
#  (cos: the deck's distance out over the tube's middle, by its radius).
DECK_ANGLE = math.acos((DECK - TUBE_MIDDLE) / TUBE_INSIDE)
DECK_HALF = TUBE_INSIDE * math.sin(DECK_ANGLE)
#  A shaft's bulkhead lies this far out of the hole's wall (back to back
#  with it), its cells this far past the shaft's round (hidden behind its
#  tube: no slit at its edge), m. A sleeve's walls start a hair out of
#  the rocket's wall (its doors' jambs end there) and reach this far
#  past the hole's wall, m.
BULKHEAD_OFF = 0.005
BULKHEAD_OVER = 0.25
SLEEVE_OFF = 0.001
SLEEVE_OVER = 0.02


@functools.lru_cache(maxsize=1)
def interiorMeshes() -> dict:
  """Returns the station's inside by look: 'inside' (its walls), 'deck'
  (the ring's floor)."""
  return {'inside': joined([shaftRows(), bulkheadRows(), sleeveRows(),
                            ringInsideRows()]),
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


def shaftRows() -> tuple:
  """Returns the four shafts' tunnels through the drum, from the hole's
  wall to its outer side (each end where its round meets them)."""
  parts = []
  for angle in _spokeAngles():
    way = (math.cos(angle), math.sin(angle), 0.0)
    side = (-math.sin(angle), math.cos(angle), 0.0)

    def wall(u: float, v: float, way: tuple = way,
             side: tuple = side) -> tuple:
      round_ = tuple(math.cos(u) * s + math.sin(u) * z for s, z in zip(
        side, (0.0, 0.0, 1.0)))
      across = SHAFT_INSIDE * math.cos(u)
      start = math.sqrt(SOCKET * SOCKET - across * across)
      end = math.sqrt(DRUM * DRUM - across * across)
      out = start + v * (end - start)
      place = tuple(out * w + SHAFT_INSIDE * r for w, r in zip(way,
                                                               round_))
      return place, tuple(-r for r in round_)

    parts.append(gridRows(wall, (0.0, TAU), (0.0, 1.0), SHAFT_CUTS))
  return joined(parts)


def bulkheadRows() -> tuple:
  """Returns the shafts' bulkheads: each on the drum's hole's wall
  across its shaft's root, facing into the shaft, its door-sized
  opening cut ('_stationmeshes.inOpening')."""
  us, vs = holeGrid()
  far = SOCKET + BULKHEAD_OFF
  rows, faces = [], []
  for u0, u1 in zip(us[:-1], us[1:]):
    for v0, v1 in zip(vs[:-1], vs[1:]):
      u, v = 0.5 * (u0 + u1), 0.5 * (v0 + v1)
      across = SOCKET * math.sin(shaftWay(u))
      if (math.hypot(across, v) > SHAFT + BULKHEAD_OVER
              or inOpening(u, v)):
        continue
      first = len(rows)
      for a, b in ((u0, v0), (u1, v0), (u1, v1), (u0, v1)):
        c, s = math.cos(a), math.sin(a)
        rows.append((far * c, far * s, b, c, s, 0.0, a, b))
      faces.extend((first, first + 1, first + 2, first, first + 2,
                    first + 3))
  return numpy.array(rows, numpy.float64), numpy.array(faces,
                                                       numpy.uint32)


def sleeveRows() -> tuple:
  """Returns the sleeves over the gap from a docked rocket's top floor's
  doors (in its head's wall, '_levels.HEAD' round) to the shafts' mouths
  in the drum's hole: each four walls round its door's doorway, facing
  in (drawn docked: the station's inside)."""
  parts = []
  half, high = DOORWAY_HALF
  near, far = HEAD + SLEEVE_OFF, SOCKET + SLEEVE_OVER
  for angle in _spokeAngles():
    way = (math.cos(angle), math.sin(angle), 0.0)
    side = (-math.sin(angle), math.cos(angle), 0.0)
    for across, up in ((side, (0.0, 0.0, 1.0)), ((0.0, 0.0, 1.0), side)):
      reach = half if across is side else high
      span = high if across is side else half
      for sign in (1.0, -1.0):

        def plate(u: float, v: float, across: tuple = across,
                  up: tuple = up, sign: float = sign, reach: float = reach,
                  span: float = span) -> tuple:
          out = near + u * (far - near)
          place = tuple(out * w + sign * reach * a + v * span * p
                        for w, a, p in zip(way, across, up))
          return place, tuple(-sign * a for a in across)

        parts.append(gridRows(plate, (0.0, 1.0), (-1.0, 1.0), (1, 2)))
  return joined(parts)


def ringInsideRows() -> tuple:
  """Returns the ring's tube inside over its deck: open where it is
  glazed ('GLAZED' round it from straight out, over its top) but for its
  frame ('frameRows'); over each terminal the ceiling's cells made anew
  finer with its guide tube's square hole cut."""
  vs = (DECK_ANGLE, TAU - DECK_ANGLE)
  nu, nv = RING_CUTS
  du, dv = TAU / nu, (vs[1] - vs[0]) / nv
  patches = []
  for angle in _spokeAngles():
    reach = math.asin(HOLE_HALF / (TUBE_MIDDLE - TUBE_INSIDE))
    i0 = math.floor((angle - reach) / du)
    i1 = math.ceil((angle + reach) / du)
    tilt = math.asin(HOLE_HALF / TUBE_INSIDE)
    j0 = math.floor((math.pi - tilt - vs[0]) / dv)
    j1 = math.ceil((math.pi + tilt - vs[0]) / dv)
    patches.append((angle, (i0 * du, i1 * du), (vs[0] + j0 * dv,
                                                vs[0] + j1 * dv)))

  def wall(u: float, v: float) -> tuple:
    c, s = math.cos(u), math.sin(u)
    out = TUBE_MIDDLE + TUBE_INSIDE * math.cos(v)
    up = TUBE_INSIDE * math.sin(v)
    return (out * c, out * s, up), (-math.cos(v) * c, -math.cos(v) * s,
                                    -math.sin(v))

  def skip(u: float, v: float) -> bool:
    return _inPatch(patches, u, v) or GLAZED < v < TAU - GLAZED

  first = next(j for j in range(nv) if vs[0] + (j + 0.5) * dv > GLAZED)
  ends = (vs[0] + first * dv, vs[1] - first * dv)
  parts = [gridRows(wall, (0.0, TAU), vs, RING_CUTS, skip),
           frameRows(wall, patches, ends)]
  for angle, us, ws in patches:

    def hole(u: float, v: float, angle: float = angle) -> bool:
      out = TUBE_MIDDLE + TUBE_INSIDE * math.cos(v)
      return (abs(out * math.sin(u - angle)) < HOLE_HALF
              and abs(TUBE_INSIDE * math.sin(v)) < HOLE_HALF
              and math.cos(v) < 0.0)

    parts.append(gridRows(wall, us, ws, PATCH_CUTS, hole))
  return joined(parts)


def frameRows(wall: object, patches: list, ends: tuple) -> tuple:
  """Returns the glass's frame on the tube's wall ('wall(u, v)': its
  place and normal into the room) over the opening (round the tube from
  'ends[0]' to 'ends[1]'): the ribs round the tube and the mullions along
  the ring (each 'FRAME_HALF' half wide; the mullions 'FRAME_IN' into
  the room, over the ribs where they cross), none in the terminals'
  patches ('patches')."""
  parts = []
  radius = TUBE_MIDDLE - TUBE_INSIDE
  half = FRAME_HALF / radius
  ribs = int(round(TAU / RIB_EVERY))

  def skip(u: float, v: float) -> bool:
    return _inPatch(patches, u, v)

  def raised(u: float, v: float) -> tuple:
    place, normal = wall(u, v)
    return tuple(p + FRAME_IN * n for p, n in zip(place, normal)), normal

  for k in range(ribs):
    u = TAU * k / ribs
    parts.append(gridRows(wall, (u - half, u + half), ends, (1, 24), skip))
  across = FRAME_HALF / TUBE_INSIDE
  for v in MULLIONS:
    parts.append(gridRows(raised, (0.0, TAU), (v - across, v + across),
                          (RING_CUTS[0], 1), skip))
  return joined(parts)


def _inPatch(patches: list, u: float, v: float) -> bool:
  """Returns whether the ring's cell whose middle is at 'u', 'v' lies in
  a terminal's patch (made anew finer)."""
  for _, us, ws in patches:
    if not ws[0] < v < ws[1]:
      continue
    for turned in (u, u - TAU, u + TAU):
      if us[0] < turned < us[1]:
        return True
  return False


def deckRows() -> tuple:
  """Returns the ring's deck: its floor all round, its picture in metres
  along it and across it."""

  def floor(u: float, v: float) -> tuple:
    angle = u / DECK
    c, s = math.cos(angle), math.sin(angle)
    return (DECK * c, DECK * s, v), (-c, -s, 0.0)

  return gridRows(floor, (0.0, TAU * DECK), (-DECK_HALF, DECK_HALF),
                  (RING_CUTS[0], DECK_CUTS))
