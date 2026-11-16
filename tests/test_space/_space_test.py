"""
SpaceTest is the base class for the tests of 'worQt.gaming.space': a
'BaseTest' adding the solar system of the day the tests were written
('systemOf'), the flight on the CPU ('flightOf'), a vessel on Terra's
pad ('padded') or on an orbit round Terra ('orbiting').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.work_test import BaseTest

from worQt.gaming.space._flight import Flight
from worQt.gaming.space._planets import PAD, solarSystemOn
from worQt.gaming.space._turns import cross, quaternionOf, unit
from worQt.gaming.space._vessel import Vessel

#  2026-11-16 00:00 (TDB): the day JPL Horizons' places below are of.
TODAY = 2461360.5
#  A frame, s.
FRAME = 1.0 / 60.0


class SpaceTest(BaseTest):
  """SpaceTest is the base class for the tests of the space package."""

  def systemOf(self, ) -> object:
    """Returns the solar system on 'TODAY'."""
    return solarSystemOn(TODAY)

  def flightOf(self, ) -> Flight:
    """Returns the flight on the CPU."""
    return Flight('cpu')

  def padded(self, system: object) -> Vessel:
    """Returns a vessel standing on Terra's pad."""
    vessel = Vessel()
    vessel.stood(system, system.named('Terra'), PAD[0], PAD[1], 0.0)
    return vessel

  def orbiting(self, system: object, low: float, high: float,
               nose: str = 'up') -> Vessel:
    """Returns a vessel at the periapsis of an orbit round Terra 'low' by
    'high' m over its ground (in its equator's plane, going east), its
    nose 'up' (away from Terra) or 'ahead', not spinning."""
    terra = system.named('Terra')
    body = system.bodies[terra]
    r, far = body.radius + low, body.radius + high
    a = 0.5 * (r + far)
    speed = math.sqrt(body.mu * (2.0 / r - 1.0 / a))
    up = unit(tuple(row[0] for row in body.tilt))
    east = unit(cross(body.pole, up))
    nose = up if nose == 'up' else east
    side = unit(cross(nose, body.pole))
    rows = tuple((side[k], cross(nose, side)[k], nose[k]) for k in range(3))
    vessel = Vessel()
    vessel.placed(terra, tuple(r * x for x in up),
                  tuple(speed * x for x in east), quaternionOf(rows),
                  (0.0, 0.0, 0.0))
    return vessel

  def flownFrames(self, flight: Flight, vessel: Vessel, system: object,
                  seconds: float) -> None:
    """Flies 'vessel' 'seconds' s a frame at a time, no leaps."""
    t = 0.0
    for _ in range(int(round(seconds / FRAME))):
      flight.flown((vessel,), system, t, FRAME)
      t += FRAME

  def assertClose(self, one: tuple, two: tuple, tolerance: float) -> None:
    """Fails unless 'one' and 'two' are within 'tolerance' apart."""
    gap = math.dist(one, two)
    self.assertLessEqual(gap, tolerance, '%r and %r are %r apart' % (
      one, two, gap))
