"""
The trains' line in the void (user, 2026-11-16: "do all the things":
a train, points, the loop eased in and out): from a buffer stop along a
headshunt to a set of points, on along the station's platform to its
edge, down the grade, once round the loop (eased in and out: its
curvature grows from nought and back, so nothing steps), along, up the
climb to the far platform. At the points a siding leaves to the left:
a reverse curve to a track 'SPACING' m beside the line, then straight
to its own buffer stop. The grade, the loop and the climb are the
loop's stage's ('phys.rail._stage'), the loop eased.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math

from worQt.phys.rail import Piece, Ribbon, bend, eased, easedLoop, straight
from worQt.phys.rail._stage import CLIMB, DROP, EASE_RADIUS, LOOP_DRIFT
from worQt.phys.rail._stage import LOOP_RADIUS, PLATFORM, RUN, SLOPE
from worQt.phys.rail._stage import gradedFor

#  The headshunt from the start's buffer stop to the points (the cart
#  waiting there, a train of two cars still stands clear of them behind
#  it, 19.5 m for its 17.1), the platform from the points to its edge,
#  m.
HEADSHUNT, STATION = 32.0, 22.0
#  Where the points are and where the platform ends, m along the line.
TOE = HEADSHUNT
EDGE = HEADSHUNT + STATION
#  How far beside the line the siding runs (track centres, m: 4.5 as on
#  a main line), the radius of its reverse curve, m (a tight turnout,
#  for shunting at a walk), how long it runs straight after, m.
SPACING, TURNOUT_RADIUS, SIDING_STRAIGHT = 4.5, 40.0, 24.0
#  How long the loop eases in and out, m (at its foot's ~22 m/s each
#  ease takes 0.36 s).
LOOP_EASE = 8.0
#  The frame's axes turned about: its left pitches the way down, its up
#  turns it left.
_DOWN, _UP = (0.0, 1.0, 0.0), (0.0, -1.0, 0.0)
_LEFT, _RIGHT = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0)


@functools.lru_cache(maxsize=1)
def mainLine() -> Ribbon:
  """The 'mainLine' function returns the line (made once): the
  headshunt, the platform, the grade down, the run in, the loop eased,
  the run out, the climb, the far platform."""
  pieces = (straight(HEADSHUNT),
            straight(STATION),
            bend(SLOPE, EASE_RADIUS, _DOWN),
            straight(gradedFor(DROP)),
            bend(SLOPE, EASE_RADIUS, _UP),
            straight(RUN)) + easedLoop(LOOP_RADIUS, LOOP_DRIFT,
                                       LOOP_EASE) + (
    straight(RUN),
    bend(SLOPE, EASE_RADIUS, _UP),
    straight(gradedFor(CLIMB)),
    bend(SLOPE, EASE_RADIUS, _DOWN),
    straight(PLATFORM))
  return Ribbon(pieces, (0.0, 0.0, DROP))


def sidingTurn() -> float:
  """The 'sidingTurn' function returns how far each half of the
  siding's reverse curve turns, rad (the two of 'TURNOUT_RADIUS' taking
  it 'SPACING' m aside)."""
  return math.acos(1.0 - SPACING / (2.0 * TURNOUT_RADIUS))


@functools.lru_cache(maxsize=1)
def sidingLine() -> Ribbon:
  """The 'sidingLine' function returns the siding (made once): from the
  points ('TOE' m along the line, as the line lies there) a curve to
  the left and one back, then straight."""
  turn = sidingTurn()
  place, frame = mainLine().frameAt(TOE)
  pieces = (bend(turn, TURNOUT_RADIUS, _LEFT),
            bend(turn, TURNOUT_RADIUS, _RIGHT),
            straight(SIDING_STRAIGHT))
  return Ribbon(pieces, tuple(float(x) for x in place), frame)


def loopSpanOf() -> tuple:
  """The 'loopSpanOf' function returns where along the line the loop
  begins and ends (its eases with it), m."""
  pieces = mainLine().pieces
  begins = sum(piece.length for piece in pieces[:6])
  return begins, begins + sum(piece.length for piece in pieces[6:9])


#  The steam train's oval (user, 2026-11-16: a steam locomotive and its
#  train; a 4-6-2's coupled wheels span 4.5 m, so it cannot take the
#  10 m loop): two straights 'OVAL_STRAIGHT' m long joined by half
#  circles of 'OVAL_RADIUS' m, each eased in and out over 'OVAL_EASE' m
#  (a main line's curves, its transitions; unbanked: at 150 m the
#  train ran its tender off at 22 m/s, a third of a g across, a tram's
#  curve; at 400 m that is ~36 m/s); level, its rails' top 'OVAL_UP' m
#  over the ground (the bed's top a centimetre over it).
OVAL_STRAIGHT, OVAL_RADIUS, OVAL_EASE = 300.0, 400.0, 60.0
OVAL_UP = 0.382


def _halfTurn() -> tuple:
  """Returns half a turn to the left of 'OVAL_RADIUS', eased in and out
  over 'OVAL_EASE' (the arc between as long as makes it half a turn)."""
  rate = (0.0, 0.0, 1.0 / OVAL_RADIUS)
  arc = math.pi * OVAL_RADIUS - OVAL_EASE
  return (eased(OVAL_EASE, (0.0, 0.0, 0.0), rate),
          Piece(arc, rate, rate),
          eased(OVAL_EASE, rate, (0.0, 0.0, 0.0)))


@functools.lru_cache(maxsize=1)
def ovalLine() -> Ribbon:
  """The 'ovalLine' function returns the oval (made once), closed: from
  the middle of its near straight along x, round to the left, back
  along the far straight and round again to where it began, its middle
  over the origin."""
  pieces = ((straight(0.5 * OVAL_STRAIGHT),) + _halfTurn()
            + (straight(OVAL_STRAIGHT),) + _halfTurn()
            + (straight(0.5 * OVAL_STRAIGHT),))
  first = Ribbon(pieces, (0.0, 0.0, OVAL_UP))
  across = float(first.frameAt(0.5 * first.length)[0][1])
  return Ribbon(pieces, (0.0, -0.5 * across, OVAL_UP))
