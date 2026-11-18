"""
TestJetpack covers Asger's jetpack (user, 2026-11-18: "It lets Asger
move with key_W in the direction faced key_S away and AD for strafing.
Have it be off until Asger opens his inventory where he can activate
it") and his headlamp ("Starting off, activated in inventory"): both
start off; on, the jetpack pushes its level's share of its thrust along
the way the keys ask (W where he looks, S back, A and D aside, two keys
at once no harder), off nothing; its levels stop at their ends; the
headlamp switches.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._headlamp import Headlamp
from worQt.gaming.space._jetpack import LEVELS, THRUST, Jetpack
from worQt.gaming.space._turns import cross, dot, norm

from . import SpaceTest


class TestJetpack(SpaceTest):
  """Tests for the jetpack and the headlamp."""

  def test_off(self) -> None:
    """Both start off; off, the jetpack pushes nothing."""
    jetpack, lamp = Jetpack(), Headlamp()
    self.assertFalse(jetpack.on)
    self.assertFalse(lamp.on)
    self.assertEqual(jetpack.pushOf((1.0, 0.0, 0.0)), (0.0, 0.0, 0.0))
    lamp.toggled()
    self.assertTrue(lamp.on)
    lamp.toggled()
    self.assertFalse(lamp.on)

  def test_levels(self) -> None:
    """Its push is its level's share of 'THRUST'; the levels stop at
    their ends."""
    jetpack = Jetpack()
    jetpack.toggled()
    for _ in range(len(LEVELS) + 2):
      jetpack.stronger()
    self.assertEqual(jetpack.thrust, THRUST * LEVELS[-1])
    for _ in range(len(LEVELS) + 2):
      jetpack.weaker()
    self.assertEqual(jetpack.thrust, THRUST * LEVELS[0])
    push = jetpack.pushOf((0.0, 0.0, 1.0))
    self.assertClose(push, (0.0, 0.0, THRUST * LEVELS[0]), 1e-12)

  def test_ways(self) -> None:
    """W pushes where he looks (up and down too), S back, A to his left,
    D to his right, two at once no harder than one; none held, none."""
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    yaw, pitch = 0.4, 0.3
    look = crewman.lookOf(yaw, pitch)
    left = cross(crewman.up, crewman.facing(yaw))
    self.assertClose(crewman.wayOf({'ahead'}, yaw, pitch), look, 1e-9)
    self.assertClose(crewman.wayOf({'back'}, yaw, pitch),
                     tuple(-x for x in look), 1e-9)
    self.assertGreater(dot(crewman.wayOf({'left'}, yaw, pitch), left),
                       0.999)
    self.assertLess(dot(crewman.wayOf({'right'}, yaw, pitch), left),
                    -0.999)
    both = crewman.wayOf({'ahead', 'left'}, yaw, pitch)
    self.assertLess(abs(norm(both) - 1.0), 1e-9)
    self.assertLess(abs(dot(both, look) - math.sqrt(0.5)), 0.05)
    self.assertEqual(crewman.wayOf(set(), yaw, pitch), (0.0, 0.0, 0.0))
    self.assertEqual(crewman.wayOf({'ahead', 'back'}, yaw, pitch),
                     (0.0, 0.0, 0.0))
