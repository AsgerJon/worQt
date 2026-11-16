"""
The loop's stage (user, 2026-11-15: "let's make a void world, like in
skyblock, where there is only enough terrain for the loop de loop"): a
track in the void from a platform 'DROP' m over the loop's foot, down a
'SLOPE' grade, along a short level run, once round a loop of
'LOOP_RADIUS' m drifting 'LOOP_DRIFT' m sideways (its way out beside its
way in), along another level run and up a climb to a platform 'CLIMB'
m up, higher than the start: whatever rolls from the start never
reaches it, rolls back and through the loop again. The grade begins and
ends on circular vertical curves of 'EASE_RADIUS' m. The loop's foot is
at height nought, the start platform's beginning at x nought, heading
along x.

With k = 0.315 (a wheelset: 1500 kg, 100 kg m^2, r0 0.46 m) a loop of
10 m wants 26.6 m of drop; 'DROP' is 30 m.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from ._piece import bend, loop, straight
from ._ribbon import Ribbon

#  The loop's radius and its sideways drift over its turn, m; the start
#  platform's height over the loop's foot and the far one's, m; the
#  grades' angle, rad, and their vertical curves' radius, m; the
#  platforms' length and the level runs' either side of the loop, m.
LOOP_RADIUS, LOOP_DRIFT = 10.0, 3.0
DROP, CLIMB = 30.0, 32.0
SLOPE, EASE_RADIUS = math.radians(30.0), 20.0
PLATFORM, RUN = 12.0, 10.0
#  The frame's left axis: turning about it pitches the way down.
_DOWN, _UP = (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)


def _graded(height: float) -> float:
  """Returns how long a straight grade must be for the track to climb or
  fall 'height' m with its two vertical curves."""
  eased = 2.0 * EASE_RADIUS * (1.0 - math.cos(SLOPE))
  if height <= eased:
    raise ValueError('%.2f m is no more than the curves alone' % height)
  return (height - eased) / math.sin(SLOPE)


@functools.lru_cache(maxsize=1)
def loopTrack() -> Ribbon:
  """The 'loopTrack' function returns the stage's track (made once): the
  start platform, the grade down, the run in, the loop, the run out,
  the climb, the far platform."""
  pieces = (straight(PLATFORM),
            bend(SLOPE, EASE_RADIUS, _DOWN),
            straight(_graded(DROP)),
            bend(SLOPE, EASE_RADIUS, _UP),
            straight(RUN),
            loop(LOOP_RADIUS, LOOP_DRIFT),
            straight(RUN),
            bend(SLOPE, EASE_RADIUS, _UP),
            straight(_graded(CLIMB)),
            bend(SLOPE, EASE_RADIUS, _DOWN),
            straight(PLATFORM))
  return Ribbon(pieces, (0.0, 0.0, DROP))


def loopSpan() -> tuple[float, float]:
  """The 'loopSpan' function returns where along the stage's track the
  loop begins and ends, m."""
  track = loopTrack()
  begins = sum(piece.length for piece in track.pieces[:5])
  return begins, begins + track.pieces[5].length


#  The island the walker starts on, under the start platform (skyblock:
#  grass on dirt, nothing under it): where it begins and ends along x,
#  how far it reaches either side, m; its grass and its dirt, m thick;
#  how far its top lies under the rails' top (the track's bed, drawn
#  along the track, stands 5 cm proud of it); where the walker stands
#  on it (x, y), m; how the walker meets it (N/m at a point, s/m, grip,
#  bristle N/m, its damping); how dense earth is, kg/m^3 (it never
#  moves: bodies of the world).
ISLAND_FROM, ISLAND_TO, ISLAND_HALF = -6.0, 14.0, 6.0
GRASS, DIRT = 0.3, 2.7
ISLAND_UNDER = 0.422
WALKER_AT = (-3.0, 3.5)
ON_GRASS = (1e6, 1.0, 0.6, 1e6, 2e3)
EARTH = 1800.0
#  Where along the track the wheelset starts, still, m: a metre into the
#  grade's first curve, so it rolls off at once (on the platform it
#  would stand).
WHEELSET_AT = 13.0


def loopStage() -> tuple:
  """The 'loopStage' function returns the loop's stage in the void (the
  walker first, standing on the island; the wheelset second, still on
  the rails 'WHEELSET_AT' m along, rolled by the rail world; the
  island's grass, then its dirt, bodies of the world the walker meets)
  and how it starts. The track itself is drawn ('loopTrack')."""
  from .._assembly import Assembly, Contact, Fixed
  from .._body import Body, State
  from .._scenes import WALKER
  from .._shape import boxShape
  from ._railworld import wheelsetOn
  from ._wheelset import wheelsetBody
  top = DROP - ISLAND_UNDER
  long, wide = ISLAND_TO - ISLAND_FROM, 2.0 * ISLAND_HALF
  middle = 0.5 * (ISLAND_FROM + ISLAND_TO)
  bodies = (WALKER.body(), wheelsetBody(),
            Body.of(boxShape(long, wide, GRASS), EARTH),
            Body.of(boxShape(long, wide, DIRT), EARTH))
  states = (State((WALKER_AT[0], WALKER_AT[1], top + WALKER.radius)),
            wheelsetOn(loopTrack(), WHEELSET_AT, 0.0),
            State((middle, 0.0, top - 0.5 * GRASS)),
            State((middle, 0.0, top - GRASS - 0.5 * DIRT)))
  connections = (Fixed(2), Fixed(3), Contact(0, 2, *ON_GRASS),
                 Contact(0, 3, *ON_GRASS))
  return Assembly(bodies, connections), states


def stageFinishes(assembly: object) -> dict:
  """The 'stageFinishes' function returns how the stage's bodies are
  drawn: the wheelset 'wheelset', the island's grass 'grass', its dirt
  'dirt'."""
  return {1: 'wheelset', 2: 'grass', 3: 'dirt'}


def loopRails() -> tuple:
  """The 'loopRails' function returns what the rail world rolls on the
  stage: its track and the wheelset's body (each body that is it)."""
  from ._wheelset import wheelsetBody
  return loopTrack(), wheelsetBody()
