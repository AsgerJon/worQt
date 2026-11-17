"""
TestVitals covers Asger's health and hunger (user, 2026-11-17: "4g would
kill Asger in 20 seconds. 3g would kill Asger in 80 seconds. 2g will not
kill Asger but will increase his need of food by 4x"; "To eat, Asger
goes to the kitchen where an endless supply of RCIR"), and the engine's
limiter ("another engine control that restricts the engine output to a
particular g"): the deaths on time, two g's hunger, a ration, starving,
mending, waking; falls (user: "Up to 1.5 Asger heights, Asger takes no
fall dmg. Falling 12 Asger heights and it's over"); the limiter caps
the push; the rations' crate within his reach only near it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cockpit import LIMITS, Cockpit
from worQt.gaming.space._instruments import limitNotch
from worQt.gaming.space._vessel import MASS, Vessel
from worQt.gaming.space._vitals import EATING, FED, FOOD, FOOD_LASTS
from worQt.gaming.space._vitals import HEALTH, RATION, TALL, Vitals

from . import FRAME, SpaceTest


class TestVitals(SpaceTest):
  """Tests for Asger's vitals and the engine's limiter."""

  def _deathAt(self, gees: float, longest: float) -> float | None:
    """Returns when Asger pulled 'gees' g dies, s (None: alive after
    'longest' s)."""
    vitals = Vitals()
    t = 0.0
    while t < longest:
      vitals.lived(FRAME, gees)
      t += FRAME
      if vitals.cause is not None:
        return t
    return None

  def test_crushed(self) -> None:
    """Four g kills him in 20 s, three in 80 s; two never (in ten
    minutes, fed)."""
    self.assertAlmostEqual(self._deathAt(4.0, 60.0), 20.0, 0)
    self.assertAlmostEqual(self._deathAt(3.0, 200.0), 80.0, 0)
    vitals = Vitals()
    for _ in range(int(600.0 / FRAME)):
      vitals.lived(FRAME, 2.0)
      if vitals.food < 2.0:
        vitals.food = FOOD
    self.assertIsNone(vitals.cause)
    self.assertEqual(vitals.health, HEALTH)

  def test_hunger(self) -> None:
    """A full stomach lasts 'FOOD_LASTS' at one g, four times less at
    two."""
    for gees, lasts in ((1.0, FOOD_LASTS), (0.0, FOOD_LASTS),
                        (2.0, FOOD_LASTS / 4.0)):
      vitals = Vitals()
      vitals.lived(lasts / 2.0, gees)
      self.assertAlmostEqual(vitals.food, FOOD / 2.0, 6, gees)

  def test_eating(self) -> None:
    """A ration takes 'EATING' s and feeds 'RATION'; full, dead or
    already eating he eats none."""
    vitals = Vitals()
    self.assertEqual(vitals.ate(), 'Asger is full')
    vitals.food = 5.0
    self.assertEqual(vitals.ate(), '')
    self.assertEqual(vitals.ate(), 'Asger is eating')
    vitals.lived(EATING - 0.1, 0.0)
    self.assertLess(vitals.food, 5.0)
    vitals.lived(0.2, 0.0)
    self.assertAlmostEqual(vitals.food, 5.0 + RATION, 1)
    self.assertEqual(vitals.meals, 1)

  def test_starving(self) -> None:
    """With nothing to eat he starves to death; fed he mends; woken he
    is whole."""
    vitals = Vitals()
    vitals.food = 0.0
    vitals.lived(30.0, 0.0)
    self.assertLess(vitals.health, HEALTH)
    self.assertGreater(vitals.hurts, 0)
    for _ in range(200):
      vitals.lived(1.0, 0.0)
    self.assertEqual(vitals.cause, 'starved')
    self.assertEqual(vitals.ate(), 'Asger is dead')
    vitals.revived()
    self.assertIsNone(vitals.cause)
    vitals.health, vitals.food = 10.0, FED + 1.0
    vitals.lived(4.0, 1.0)
    self.assertGreater(vitals.health, 10.0)

  def test_falls(self) -> None:
    """Meeting something as fast as a fall of 1.5 of his heights hurts
    him not; of 12, kills him; between, as the height."""
    for heights, left in ((1.4, HEALTH), (6.75, HEALTH / 2.0),
                          (12.0, 0.0)):
      vitals = Vitals()
      vitals.fell(math.sqrt(2.0 * G0 * heights * TALL))
      self.assertAlmostEqual(vitals.health, left, 6, heights)
    self.assertIsNotNone(vitals.cause)
    self.assertGreater(vitals.hurts, 0)

  def test_limiter(self) -> None:
    """The limiter caps the push at its g whatever the throttle; at its
    last notch the engine is whole; a limit of nothing is refused."""
    engine = Vessel().engine
    self.assertEqual(limitNotch(engine), len(LIMITS) - 1)
    engine.throttled(1.0)
    whole = engine.push
    engine.limited(1.0 * G0 * MASS)
    self.assertAlmostEqual(engine.push / (MASS * G0), 1.0, 9)
    self.assertEqual(limitNotch(engine), LIMITS.index(1.0))
    engine.throttled(0.1)
    self.assertAlmostEqual(engine.push, 0.1 * whole, 6)
    engine.limited(10.0 * whole)
    engine.throttled(1.0)
    self.assertAlmostEqual(engine.push, whole, 6)
    with self.assertRaises(ValueError):
      engine.limited(0.0)

  def test_rations(self) -> None:
    """The rations' crate is out of his reach from his chair, his to eat
    from looked at near it."""
    cockpit = Cockpit()
    crate = cockpit.galley[0]
    self.assertEqual(crate.action, 'eat')
    cockpit.gotUp()
    crewman = cockpit.crewman
    front = crate.axes[1]
    crewman.middle = (crate.centre[0] + front[0], crate.centre[1]
                      + front[1], crewman.middle[2])
    crewman.ahead = (-front[0], -front[1], 0.0)
    way = tuple(c - e for c, e in zip(crate.centre, cockpit.eye()))
    size = math.sqrt(sum(x * x for x in way))
    cockpit.yaw, cockpit.pitch = 0.0, math.asin(way[2] / size)
    self.assertIs(cockpit.lookedAt(), crate)
    cockpit.strappedIn()
    self.assertIsNot(cockpit.lookedAt(), crate)
