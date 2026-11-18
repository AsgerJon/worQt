"""
TestPushedBack covers what Asger does to the rocket (user, 2026-11-18:
"PHYSICS MUST BE REAL"; the jetpack: its fans blow the cabin's air,
which carries their push to the walls): standing on its floor he
weighs on it; jumping off it weightless he kicks it the other way, and
landing on the ceiling he gives that back; his jetpack pushes it back
as hard as it pushes him; sitting down, his chair takes what he moved
with. The vessel so pushed changes its velocity and spin by the push
over its mass and moments, and that is felt over the next frame, once.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import STILL, CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._crewman import HEFT
from worQt.gaming.space._turns import cross, rotated
from worQt.gaming.space._vessel import INERTIA, MASS, Vessel

from . import FRAME, SpaceTest


class TestPushedBack(SpaceTest):
  """Tests for the cabin pushing the vessel back."""

  #  The cabin's kernels compile and step on the CPU here: minutes.
  __time_out__ = 900.0

  def _summed(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, frames: int, want: tuple,
              jet: tuple = (0.0, 0.0, 0.0)) -> tuple:
    """Steps 'world' 'frames' frames (Asger's legs as 'want' asks, its
    leap the first frame only, his jetpack 'jet' m/s²) and returns what
    they pushed back by, summed (N s, N m s): Asger's and the loose
    things' ('asgerPushed', 'pushedBack'; here, in the cabin, all the
    vessel's)."""
    push, twist = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    for k in range(frames):
      leap = want[3] if k == 0 else (0.0, 0.0, 0.0)
      world.stepped(FRAME, meter, cockpit.crewman, want[:3] + (leap,),
                    None, jet)
      for back, turned in (world.pushedBack, world.asgerPushed):
        push = [a + b for a, b in zip(push, back)]
        twist = [a + b for a, b in zip(twist, turned)]
    return tuple(push), tuple(twist)

  def test_weight(self) -> None:
    """Standing on the floor in one g he pushes it down by his weight,
    each second his mass times g, at his middle."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    self._summed(world, meter, cockpit, 30, STILL)
    frames = 60
    push, twist = self._summed(world, meter, cockpit, frames, STILL)
    seconds = frames * FRAME
    self.assertLess(abs(push[2] + HEFT * G0 * seconds),
                    0.02 * HEFT * G0 * seconds)
    self.assertLess(abs(push[0]) + abs(push[1]), 1.0)
    middle = cockpit.crewman.middle
    lever = cross(middle, (0.0, 0.0, -HEFT * G0 * seconds))
    self.assertClose(twist, lever, 0.03 * HEFT * G0 * seconds)

  def test_leap(self) -> None:
    """Weightless, pushing off the floor kicks the vessel down as hard as
    it sends him up; meeting the walls overhead slows him, and gives it
    back: all along, the vessel's push and his motion sum to none."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    cockpit.gotUp()
    crewman = cockpit.crewman
    self._summed(world, meter, cockpit, 6, STILL)
    leap = crewman.leapOf((0.0, 0.0, 0.0))
    push, _ = self._summed(world, meter, cockpit, 1, STILL[:3] + (leap,))
    self.assertLess(abs(push[2] + HEFT * leap[2]), 0.05 * HEFT * leap[2])
    total = list(push)
    met = False
    for _ in range(240):
      back, _ = self._summed(world, meter, cockpit, 1, STILL)
      total = [a + b for a, b in zip(total, back)]
      met = met or crewman.touches
    self.assertTrue(met)
    self.assertLess(crewman.velocity[2], 0.9 * leap[2])
    for k in range(3):
      self.assertLess(abs(total[k] + HEFT * crewman.velocity[k]), 0.02)

  def test_jet(self) -> None:
    """Floating free, his jetpack pushes the vessel back as hard as it
    pushes him (but for the air's little drag on him, the vessel's
    too)."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    cockpit.gotUp()
    crewman = cockpit.crewman
    self._summed(world, meter, cockpit, 6, STILL)
    leap = crewman.leapOf((0.0, 0.0, 0.0))
    self._summed(world, meter, cockpit, 12, STILL[:3] + (
      tuple(0.25 * x for x in leap),))
    self.assertFalse(crewman.touches)
    force = 14.0
    frames = 30
    began = crewman.velocity[0]
    push, _ = self._summed(world, meter, cockpit, frames, STILL,
                           (force / HEFT, 0.0, 0.0))
    seconds = frames * FRAME
    self.assertLess(abs(push[0] + force * seconds), 0.03 * force * seconds)
    gained = HEFT * (crewman.velocity[0] - began)
    self.assertLess(abs(push[0] + gained), 1e-3 * force * seconds + 1e-3)

  def test_seated(self) -> None:
    """Sitting down, his chair stops him: what he moved with pushes the
    vessel."""
    cockpit = Cockpit()
    world = CabinWorld('cpu')
    meter = self.stillMeter()
    cockpit.gotUp()
    crewman = cockpit.crewman
    self._summed(world, meter, cockpit, 6, STILL, (0.2, 0.0, 0.0))
    moving = crewman.velocity
    self.assertGreater(moving[0], 0.01)
    self.assertTrue(cockpit.satDown())
    world.stepped(FRAME, meter, crewman, STILL)
    push, _ = world.pushedBack
    self.assertClose(push, tuple(HEFT * v for v in moving), 1e-6)

  def test_kicked(self) -> None:
    """Pushed between frames, the vessel's velocity and spin change by
    the push over its mass and its moments; the change is felt over the
    next frame, once."""
    vessel = Vessel()
    vessel.felt, vessel.spinning = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    turn = (0.9238795325112867, 0.0, 0.0, 0.3826834323650898)
    vessel.placed(0, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), turn,
                  (0.0, 0.0, 0.0))
    vessel.kicked((MASS * 0.001, 0.0, 0.0), (0.0, 0.0, INERTIA[2] * 0.002))
    self.assertClose(vessel.velocity, rotated(turn, (0.001, 0.0, 0.0)),
                     1e-12)
    self.assertClose(vessel.spin, (0.0, 0.0, 0.002), 1e-12)
    meter = Accelerometer()
    meter.measured(vessel, 0.5)
    self.assertClose(meter.felt, (0.002, 0.0, 0.0), 1e-9)
    self.assertClose(meter.speeding, (0.0, 0.0, 0.004), 1e-12)
    meter.measured(vessel, 0.5)
    self.assertClose(meter.felt, (0.0, 0.0, 0.0), 1e-12)
    self.assertClose(meter.speeding, (0.0, 0.0, 0.0), 1e-12)
