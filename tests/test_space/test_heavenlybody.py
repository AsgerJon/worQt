"""
TestHeavenlyBody covers the heavenly bodies (user, 2026-11-16: "each
heavenly body is a vector of dofs, a vector function in time. other
data points are fixed immutable"): flown, each pulling every other,
near where its parent alone would have it a day on; a leap's fold
changing nothing but where time starts; Terra
true to the Earth with the user's g of 9.82; its turn about its pole;
the moons' reaches apart.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from . import SpaceTest


class TestHeavenlyBody(SpaceTest):
  """Tests for 'HeavenlyBody'."""

  def test_period(self) -> None:
    """A day on, every body but Sol is near where the path it was on (its
    'conic': its parent alone pulling it) has it: the others' pulls bend
    it only a little."""
    system = self.systemOf()
    day = 86400.0
    for index, body in enumerate(system.bodies[1:], 1):
      flown = system.stateOf(index, day)[0]
      alone = body.conic.stateAt(day)[0]
      moved = math.dist(system.stateOf(index, 0.0)[0], flown)
      self.assertLess(math.dist(flown, alone), 0.01 * moved, body.name)

  def test_fold(self) -> None:
    """Folded 's' s, a body is at time nought where it was at 's', and
    turned as it was then."""
    system = self.systemOf()
    s = 3.7e5
    places = [system.stateOf(k, s)[0] for k in range(len(system.bodies))]
    turns = [body.turnAt(s) for body in system.bodies]
    system.fold(s)
    for k, body in enumerate(system.bodies):
      self.assertClose(system.stateOf(k, 0.0)[0], places[k], 1e-6 * max(
        1.0, math.dist(places[k], (0.0, 0.0, 0.0))))
      for row, again in zip(turns[k], body.turnAt(0.0)):
        self.assertClose(row, again, 1e-12)

  def test_terra(self) -> None:
    """Terra is the Earth: 6371 km, g 9.82, a sidereal day of 86164 s,
    its pole 23.44 degrees off the ecliptic's toward the solstice."""
    system = self.systemOf()
    terra = system.bodies[system.named('Terra')]
    self.assertEqual(terra.radius, 6.371e6)
    self.assertAlmostEqual(terra.gravity, 9.82, 2)
    self.assertAlmostEqual(2.0 * math.pi / terra.spin, 86164.1, 0)
    self.assertAlmostEqual(math.degrees(math.acos(terra.pole[2])),
                           23.44, 2)
    self.assertGreater(terra.pole[1], 0.0)
    self.assertIsNotNone(terra.air)

  def test_spin(self) -> None:
    """A body's turn takes its own z to its pole always, and is the same
    again after a sidereal turn."""
    system = self.systemOf()
    for body in system.bodies:
      for t in (0.0, 1e4, 3e5):
        turn = body.turnAt(t)
        self.assertClose(tuple(row[2] for row in turn), body.pole, 1e-12)
      day = 2.0 * math.pi / body.spin
      for one, two in zip(body.turnAt(0.0), body.turnAt(day)):
        self.assertClose(one, two, 1e-9)

  def test_reach(self) -> None:
    """Luna's reach is the Moon's sphere of influence (66 000 km);
    Terra's under a million km; the two moons' reaches never meet."""
    system = self.systemOf()
    terra = system.bodies[system.named('Terra')]
    luna = system.bodies[system.named('Luna')]
    mani = system.bodies[system.named('Mani')]
    self.assertLess(abs(luna.reach / 66.2e6 - 1.0), 0.02)
    self.assertLess(terra.reach, 1e9)
    gap = mani.conic.periapsis - luna.conic.apoapsis
    self.assertGreater(gap, luna.reach + mani.reach)
