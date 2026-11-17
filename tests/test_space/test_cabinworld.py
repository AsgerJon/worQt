"""
TestCabinWorld covers what moves in the cabin, on the device (the CPU
here; user, 2026-11-17: "when can Asger get up and float around in
micro-gravity?"; the loose things "FAFO rules"): the loose things rest
where they are, on the pad or weightless; Asger up stands on the floor
under four g, walks in one, pushes off weightless and drifts on, thuds
landing from a jump (as fast as he jumped: it may hurt him); the
gravity gun pulls him to a magic bolt and holds him there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._bolts import holdOf, rocketBolts
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld, restingLoose
from worQt.gaming.space._cockpit import FLOOR, Cockpit
from worQt.gaming.space._crewman import PUSH

from . import FRAME, SpaceTest

#  Asger's legs at rest: nothing wanted, no leap.
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0), 0)


class TestCabinWorld(SpaceTest):
  """Tests for the cabin's world."""

  #  The kernels compile and step on the CPU here (a frame of 134 bodies
  #  some 0.1 s): minutes, not the default half minute.
  __time_out__ = 900.0

  def _stepped(self, world: CabinWorld, meter: Accelerometer,
               cockpit: Cockpit, seconds: float, want: tuple) -> None:
    """Steps 'world' 'seconds' s a frame at a time, Asger's legs as
    'want' asks (its leap the first frame only)."""
    for k in range(int(round(seconds / FRAME))):
      leap = want[3] if k == 0 else (0.0, 0.0, 0.0)
      world.stepped(FRAME, meter, cockpit.crewman,
                    want[:3] + (leap, want[4]))

  def _moved(self, world: CabinWorld) -> float:
    """Returns how far the loose thing that moved most is from where it
    rests, m."""
    return max(math.dist(now[0], rest[0]) for now, rest in zip(
      world.shown(), restingLoose()))

  def test_resting(self) -> None:
    """On the pad (one g up) and weightless alike the loose things stay
    where they rest."""
    cockpit = Cockpit()
    for felt in ((0.0, 0.0, G0), (0.0, 0.0, 0.0)):
      world, meter = CabinWorld('cpu'), Accelerometer()
      meter.felt = felt
      self._stepped(world, meter, cockpit, 1.0, STILL)
      self.assertLess(self._moved(world), 0.005, felt)

  def test_standing(self) -> None:
    """Up under four g he stands on the floor; in one g he walks back
    from his chair at most at his stride."""
    cockpit, meter = Cockpit(), Accelerometer()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, 4.0 * G0)
    cockpit.gotUp()
    self._stepped(world, meter, cockpit, 1.0, STILL)
    crewman = cockpit.crewman
    self.assertLess(abs(crewman.soles()[2] - FLOOR), 0.02)
    self.assertTrue(crewman.touches)
    meter.felt = (0.0, 0.0, G0)
    began = crewman.middle
    for _ in range(60):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      want = crewman.wantOf({'back'}, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0), 0))
    gone = began[0] - crewman.middle[0]
    self.assertGreater(gone, 1.5)
    self.assertLess(gone, 3.1)

  def test_floating(self) -> None:
    """Weightless he pushes off the floor and drifts on up, slowing
    only a little in the air."""
    cockpit, meter = Cockpit(), Accelerometer()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, 0.0)
    cockpit.gotUp()
    crewman = cockpit.crewman
    self._stepped(world, meter, cockpit, 0.1, STILL)
    self.assertTrue(crewman.touches)
    leap = crewman.leapOf((0.0, 0.0, 0.0))
    self.assertClose(leap, (0.0, 0.0, PUSH), 1e-6)
    low = crewman.middle[2]
    self._stepped(world, meter, cockpit, 0.5, STILL[:3] + (leap, 0))
    self.assertGreater(crewman.middle[2] - low, 0.9)
    self.assertGreater(crewman.velocity[2], 0.95 * PUSH)
    self.assertFalse(crewman.touches)

  def test_thud(self) -> None:
    """Landing from a jump in one g thuds, and lands about as fast as
    he jumped."""
    cockpit, meter = Cockpit(), Accelerometer()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    self._stepped(world, meter, cockpit, 0.2, STILL)
    crewman = cockpit.crewman
    leap = crewman.leapOf((0.0, 0.0, -G0))
    before, landed = world.thuds, 0.0
    for k in range(60):
      world.stepped(FRAME, meter, crewman, STILL[:3] + (
        leap if k == 0 else (0.0, 0.0, 0.0), 0))
      landed = max(landed, world.landed)
    self.assertGreater(world.thuds, before)
    self.assertLess(abs(landed - leap[2]), 0.5)

  def test_towed(self) -> None:
    """Weightless, the gravity gun pulls him to the nearest magic bolt on
    the wall and holds him there, never faster than its speed."""
    cockpit, meter = Cockpit(), Accelerometer()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, 0.0)
    cockpit.gotUp()
    crewman = cockpit.crewman
    bolts = rocketBolts()
    walls = [j for j, (_, way) in enumerate(bolts) if abs(way[2]) < 0.5]
    k = min(walls, key=lambda j: math.dist(holdOf(bolts[j]),
                                           crewman.middle))
    crewman.towed(k, holdOf(bolts[k]))
    fastest = 0.0
    for _ in range(int(round(4.0 / FRAME))):
      world.stepped(FRAME, meter, crewman, STILL)
      fastest = max(fastest, math.hypot(*crewman.velocity))
    self.assertLess(math.dist(crewman.middle, holdOf(bolts[k])), 0.1)
    self.assertLess(fastest, 6.1)
    self.assertLess(math.hypot(*crewman.velocity), 0.1)
