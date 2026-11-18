"""
TestNight covers night, morning and Asger's sleep (user, 2026-11-17:
"Asger should be able to key_E into bed to advance the time to morning
if it is dark, otherwise it should say like in Minecraft, 'you can only
sleep at night'"): dark is the anchor's shadow; on the pad the morning
is its sunrise and a little, the rocket carried round with the ground
through the night to where it stands then; in orbit it is the way out
of the shadow; by day there is none; the bed is looked at and worked
as the ration crate is; the screen darkens, time is sent on, it
lightens.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._furnishings import bedBox
from worQt.gaming.space._night import MORNING, isDark, morningIn, restWhy
from worQt.gaming.space._night import shineOf
from worQt.gaming.space._planets import PAD
from worQt.gaming.space._sleep import FALL, WAKE, Sleep
from worQt.gaming.space._timekeeper import Timekeeper
from worQt.gaming.space._turns import norm, unit
from worQt.gaming.space._vessel import Vessel

from . import SpaceTest


class TestNight(SpaceTest):
  """Tests for the night, the morning and the sleep."""

  def test_shine(self) -> None:
    """On the day side all the sunlight; in the shadow none; at its
    edge half."""
    sun = (1.0, 0.0, 0.0)
    self.assertEqual(shineOf(6e6, (-7e6, 0.0, 0.0), sun), 1.0)
    self.assertEqual(shineOf(6e6, (7e6, 0.0, 0.0), sun), 0.0)
    self.assertAlmostEqual(shineOf(6e6, (7e6, 6e6, 0.0), sun), 0.5)

  def test_pad(self) -> None:
    """At midnight on the pad (lying on the prime meridian) it is dark;
    the morning comes some six hours on; carried round with the ground
    and time leapt there, the rocket stands on the pad as it would
    then, in the light, and there is no morning to sleep to."""
    system = self.systemOf()
    keeper = Timekeeper(system)
    vessel = self.padded(system)
    vessel.touching = 4
    self.assertTrue(isDark(system, vessel, 0.0))
    wait = morningIn(system, vessel, 0.0)
    self.assertIsNotNone(wait)
    self.assertGreater(wait, 5.0 * 3600.0)
    self.assertLess(wait, 7.5 * 3600.0)
    self.assertTrue(isDark(system, vessel, 0.0))
    vessel.carried(system, wait)
    keeper.leapt(wait)
    self.assertEqual(keeper.now, 0.0)
    self.assertAlmostEqual(keeper.elapsed, wait)
    self.assertFalse(isDark(system, vessel, 0.0))
    self.assertIsNone(morningIn(system, vessel, 0.0))
    stood = Vessel()
    stood.stood(system, system.named('Terra'), PAD[0], PAD[1], 0.0)
    self.assertLess(math.dist(stood.place, vessel.place), 0.01)
    self.assertLess(math.dist(stood.velocity, vessel.velocity), 1e-6)
    same = abs(sum(a * b for a, b in zip(stood.turn, vessel.turn)))
    self.assertAlmostEqual(same, 1.0, 9)

  def test_orbit(self) -> None:
    """In orbit, in Terra's shadow, the morning is the way out of it,
    within half a turn; there the sun shines."""
    system = self.systemOf()
    terra = system.named('Terra')
    body = system.bodies[terra]
    vessel = self.orbiting(system, 400e3, 400e3)
    conic = vessel.conicOf(system)
    for k in range(200):
      if isDark(system, vessel, 0.0):
        break
      place, velocity = conic.stateAt(30.0 * (k + 1))
      vessel.placed(terra, place, velocity, vessel.turn, vessel.spin)
    self.assertTrue(isDark(system, vessel, 0.0))
    wait = morningIn(system, vessel, 0.0)
    self.assertIsNotNone(wait)
    self.assertLess(wait, 0.5 * conic.period + MORNING)
    there = vessel.conicOf(system).stateAt(wait)[0]
    sol = system.relative(0, terra, wait)[0]
    sun = unit(tuple(p - s for p, s in zip(there, sol)))
    self.assertEqual(shineOf(body.radius, there, sun), 1.0)
    self.assertGreater(norm(there), body.radius)

  def test_bed(self) -> None:
    """The bed is worked as the ration crate is: looked at within reach
    (E), sleeping till morning."""
    cockpit = Cockpit()
    bed = [c for c in cockpit.household if c.action == 'sleep']
    self.assertEqual(len(bed), 1)
    self.assertEqual(bed[0].key, 'E')
    self.assertEqual(bed[0].peep.prompt(), 'Sleep till morning')
    middle, axes, half = bedBox()
    eye = tuple(m + 1.0 * a + 0.9 * u for m, a, u in zip(
      middle, axes[1], axes[2]))
    way = unit(tuple(m - e for m, e in zip(middle, eye)))
    self.assertIsNotNone(bed[0].hitBy(eye, way))

  def test_sleep(self) -> None:
    """Lain down, the screen darkens over 'FALL' s; then time is due to
    be sent on (once); woken, it lightens over 'WAKE' s and the sleep
    ends."""
    sleep = Sleep()
    self.assertEqual(sleep.shade(5.0), 0.0)
    sleep.lay(10.0, 3600.0, 100.0)
    self.assertAlmostEqual(sleep.until, 3700.0)
    self.assertAlmostEqual(sleep.shade(10.0 + 0.5 * FALL), 0.5)
    self.assertFalse(sleep.due(10.0 + 0.5 * FALL))
    self.assertTrue(sleep.due(10.0 + FALL))
    sleep.sent = True
    self.assertFalse(sleep.due(11.0 + FALL))
    self.assertEqual(sleep.shade(20.0), 1.0)
    sleep.waking(30.0)
    sleep.waking(31.0)
    self.assertAlmostEqual(sleep.shade(30.0 + 0.5 * WAKE), 0.5)
    self.assertTrue(sleep.on)
    self.assertEqual(sleep.shade(30.0 + 1.01 * WAKE), 0.0)
    self.assertFalse(sleep.on)

  def test_rest(self) -> None:
    """Standing still on its legs on the pad the rocket is at rest (a
    night may be skipped); off a leg, moving or rocking it is not
    (user, 2026-11-18: "PHYSICS MUST BE REAL")."""
    system = self.systemOf()
    vessel = self.padded(system)
    vessel.touching = len(vessel.legs)
    self.assertEqual(restWhy(vessel, system), '')
    vessel.touching = len(vessel.legs) - 1
    self.assertIn('legs', restWhy(vessel, system))
    vessel.touching = len(vessel.legs)
    vessel.placed(vessel.anchor, vessel.place, tuple(
      v + 0.1 * u for v, u in zip(vessel.velocity, (1.0, 0.0, 0.0))),
                  vessel.turn, vessel.spin)
    self.assertIn('moving', restWhy(vessel, system))
    vessel = self.padded(system)
    vessel.touching = len(vessel.legs)
    rocked = tuple(s + d for s, d in zip(vessel.spin, (0.01, 0.0, 0.0)))
    vessel.placed(vessel.anchor, vessel.place, vessel.velocity, vessel.turn,
                  rocked)
    self.assertIn('rocking', restWhy(vessel, system))
