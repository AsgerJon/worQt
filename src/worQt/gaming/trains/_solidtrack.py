"""
The trains' track made solid (user, 2026-11-15: "the curvy bit of the
track does not appear to have collision with the Avatar"; 2026-11-16,
of the steam train's oval: "make trains have collision and all that"):
a track cut into straight pieces lying within 'SAG' of its curve
('chunksOf'), each a body held still ('chunkBody': its bed, its
sleepers, the two rails' heads, not drawn: the track's dress is), and a
buffer stop past an end ('stopBody': a beam across on two posts).
Shared by the loop's world and the oval's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._body import Body, State
from worQt.phys._shape import boxShape
from worQt.phys._vectors import UNTURNED, turnOf
from worQt.phys.rail._stage import EARTH
from worQt.phys.rail._trackshape import BED_DEEP, BED_HALF, BED_TOP, GAUGE
from worQt.phys.rail._trackshape import RAIL_SECTION, SLEEPER_DEEP
from worQt.phys.rail._trackshape import SLEEPER_HALF, SLEEPER_LONG
from worQt.phys.rail._trackshape import SLEEPER_PITCH, SLEEPER_TOP

#  The track is solid in straight pieces lying within 'SAG' m of its
#  curve (1.2 m long on the loop, two sleepers), 'CHUNK' m long at most
#  (on its straights: fewer bodies for every step to go over); a rail's
#  head, as wide and as tall as the rail, m.
SAG, CHUNK = 0.018, 12.0
RAIL_WIDE = RAIL_SECTION[1][0] - RAIL_SECTION[0][0]
RAIL_HIGH = -RAIL_SECTION[6][1]
#  A buffer stop's beam: m thick along the track, wide; its posts m
#  square; steel, kg/m³.
BEAM, BEAM_WIDE = 0.3, 2.6
POST = 0.2
STEEL = 7850.0


def chunksOf(ribbon: object, sag: float = SAG,
             longest: float = CHUNK) -> list:
  """The 'chunksOf' function returns where the track along 'ribbon' is
  cut into its solid pieces (from, to, m along): each of its own pieces
  cut evenly into lengths whose sag over its sharpest curve stays within
  'sag' (L^2 k / 8), 'longest' at most."""
  out, s = [], 0.0
  for piece in ribbon.pieces:
    sharpest = max(math.sqrt(sum(x * x for x in piece.start)),
                   math.sqrt(sum(x * x for x in piece.end)))
    most = longest if sharpest <= 0.0 else min(
      longest, math.sqrt(8.0 * sag / sharpest))
    count = max(1, math.ceil(piece.length / most - 1e-9))
    for k in range(count):
      out.append((s + piece.length * k / count,
                  s + piece.length * (k + 1) / count))
    s += piece.length
  return out


def chunkBody(begins: float, ends: float) -> Body:
  """The 'chunkBody' function returns the track from 'begins' to 'ends'
  m along as one body, straight along the track's frame at its middle
  (its own frame's origin there, on the rails' top): the bed, the
  sleepers whose middles lie in it, the two rails' heads, each a box."""
  middle, long = 0.5 * (begins + ends), ends - begins
  shape = boxShape(long, 2.0 * BED_HALF, BED_DEEP).moved(
    (0.0, 0.0, BED_TOP - 0.5 * BED_DEEP), UNTURNED)
  first = math.ceil((begins - 0.5 * SLEEPER_PITCH) / SLEEPER_PITCH)
  at = (first + 0.5) * SLEEPER_PITCH
  while at < ends:
    shape = shape.joined(boxShape(
      SLEEPER_LONG, 2.0 * SLEEPER_HALF, SLEEPER_DEEP).moved(
      (at - middle, 0.0, SLEEPER_TOP - 0.5 * SLEEPER_DEEP), UNTURNED))
    at += SLEEPER_PITCH
  for side in (-0.5 * GAUGE, 0.5 * GAUGE):
    shape = shape.joined(boxShape(long, RAIL_WIDE, RAIL_HIGH).moved(
      (0.0, side, -0.5 * RAIL_HIGH), UNTURNED))
  return Body.of(shape, EARTH)


def stopBody(way: float, height: float, wide: float = BEAM_WIDE) -> Body:
  """The 'stopBody' function returns a buffer stop past an end of a
  track ('way': -1 its start, 1 its end), its own frame's origin on the
  rails' top at that end: a steel beam across, 'height' m deep (its top
  and bottom over the rails' top, m), 'wide' m wide, its face at the
  origin, on two posts down to the bed."""
  low, high = height
  beam = boxShape(BEAM, wide, high - low).moved(
    (way * 0.5 * BEAM, 0.0, 0.5 * (low + high)), UNTURNED)
  bottom = BED_TOP - BED_DEEP
  for side in (-0.6, 0.6):
    beam = beam.joined(boxShape(POST, POST, low - bottom).moved(
      (way * 0.5 * BEAM, side, 0.5 * (low + bottom)), UNTURNED))
  return Body.of(beam, STEEL)


def stateOn(ribbon: object, along: float, body: Body) -> State:
  """The 'stateOn' function returns 'body' standing still with its own
  frame's origin 'along' m on 'ribbon', turned as the track there."""
  place, frame = ribbon.frameAt(along)
  rows = tuple(tuple(float(x) for x in row) for row in frame)
  centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                       for j in range(3))
                 for i in range(3))
  return State(centre, turnOf(rows))
