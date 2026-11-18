"""
TestHoist covers a lift's cage on its motor (user, 2026-11-18: "PHYSICS
MUST BE REAL"; '_hoist'): it runs to its stop and its brake holds it
there; pulled against its run it gets there later, the harder the
later, its motor no harder than its most; too heavy for its motor it
cannot climb at all; the tower's lift and the station's elevators run
on it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._elevator import DECK_STOP, HUB_STOP, Elevator
from worQt.gaming.space._hoist import hoisted
from worQt.gaming.space._station import SPIN
from worQt.gaming.space._towerlift import FOOT, TOP, TowerLift

from . import SpaceTest

FRAME = 1.0 / 60.0


class TestHoist(SpaceTest):
  """Tests for the lifts on their motors."""

  def _run(self, mass: float, along: float, most: float) -> float:
    """Returns how long a cage of 'mass' kg takes 20 m up, pulled
    'along' m/s², its motor's most 'most' N ('inf': it never gets
    there)."""
    floor, speed, target, t = 0.0, 0.0, 20.0, 0.0
    while target is not None:
      floor, speed, target, _ = hoisted(floor, speed, target, FRAME, along,
                                        mass, most, 1.5, 4.0)
      t += FRAME
      if t > 120.0:
        return math.inf
    self.assertEqual(floor, 20.0)
    return t

  def test_run(self) -> None:
    """It gets to its stop and stands there, held; pulled against its
    run, later; too heavy for its motor, never."""
    free = self._run(1000.0, 0.0, 20e3)
    loaded = self._run(1000.0, -G0, 12e3)
    self.assertLess(free, loaded)
    self.assertEqual(self._run(1000.0, -G0, 9e3), math.inf)
    floor, speed, target, faster = hoisted(5.0, 0.0, None, 1.0, -G0,
                                           1000.0, 1e3, 1.5, 4.0)
    self.assertEqual((floor, speed, target, faster), (5.0, 0.0, None, 0.0))

  def test_lifts(self) -> None:
    """The tower's lift takes a rider down to the ground and stops there;
    a station's elevator takes him out to the deck against the turning's
    pull, at most 'FAST'."""
    lift = TowerLift()
    lift.sent(FOOT)
    for _ in range(int(60.0 / FRAME)):
      lift.moved(FRAME, -G0, 80.0)
      if lift.target is None:
        break
    self.assertTrue(lift.atFoot)
    elevator = Elevator()
    elevator.sent(DECK_STOP)
    fastest = 0.0
    for _ in range(int(120.0 / FRAME)):
      elevator.moved(FRAME, SPIN * SPIN * elevator.floor, 80.0)
      fastest = max(fastest, abs(elevator.speed))
      if elevator.target is None:
        break
    self.assertTrue(elevator.atDeck)
    self.assertLess(fastest, 30.0 + 1e-6)
    self.assertGreater(DECK_STOP - HUB_STOP, 800.0)
    self.assertLess(TOP - FOOT, 60.0)
