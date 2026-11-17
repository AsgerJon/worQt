"""
TestLaunchTower covers the launch tower Asger starts in (user,
2026-11-17: "We *must* have the ability to walk around in the dark
before getting in. Have us start inside a building level with the
walkway. There should be light on. An EXIT sign should point us to a
stair case and to an elevator that can take us to the ground"): its
rooms join (the hall, the stairwell, the lift's shaft, their doorways,
the yard round the rocket's body), its flights climb from the ground to
the hall landing on landing, the lift rides between its stops opening
its doors only there; Asger walks up a flight, and rides the lift down
standing on its floor.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import FLOOR, Cockpit
from worQt.gaming.space._crewman import MIDDLE, STEP
from worQt.gaming.space._launchtower import FLIGHTS, GROUND, HALL
from worQt.gaming.space._launchtower import LIFT_FOOT, LIFT_TOP, SHAFT
from worQt.gaming.space._launchtower import STAIR_TOP, STAIRWELL, START
from worQt.gaming.space._launchtower import STEPS
from worQt.gaming.space._launchtower import flightOf, groundsInside
from worQt.gaming.space._launchtower import landingLevel, rise, towerSolids
from worQt.gaming.space._towerlift import FAST, FOOT, TOP, TowerLift

from . import FRAME, SpaceTest


class TestLaunchTower(SpaceTest):
  """Tests for the launch tower."""

  #  The cabin's kernels step on the CPU here: minutes, not half one.
  __time_out__ = 900.0

  def test_rooms(self) -> None:
    """Asger's start is in the hall; the stairwell, the shaft and the
    doorways are rooms; the yard is round the rocket's body, not in it;
    the lift's doors are rooms only where its car stands."""
    soles = START[0]
    self.assertGreater(groundsInside((soles[0], soles[1], soles[2] + 1.0),
                                     False, False), 0.9)
    self.assertGreater(groundsInside((-21.0, -1.0, FLOOR - 20.0), False,
                                     False), 0.4)
    self.assertGreater(groundsInside((-30.0, 0.0, GROUND + 1.0), False,
                                     False), 0.9)
    self.assertLess(groundsInside((-3.0, 0.0, GROUND + 1.0), False,
                                  False), 0.0)
    self.assertGreater(groundsInside((-18.6, -1.5, FLOOR + 1.0), False,
                                     False), 0.3)
    self.assertLess(groundsInside((-18.6, -2.9, FLOOR + 1.0), False,
                                  False), 0.0)
    top = tuple(0.5 * (a + b) for a, b in zip(*LIFT_TOP))
    door = (-18.6, top[1], top[2])
    self.assertLess(groundsInside(door, False, False), 0.0)
    self.assertGreater(groundsInside(door, True, False), 0.3)
    foot = tuple(0.5 * (a + b) for a, b in zip(*LIFT_FOOT))
    foot = (foot[0], 3.4, foot[2])
    self.assertGreater(groundsInside(foot, False, True), 0.2)

  def test_flights(self) -> None:
    """The flights climb from the ground to the hall's floor, each from
    the landing the last ended on, at a stair's slope, each step a solid
    he steps up; the top landing is by the hall's doorway."""
    self.assertAlmostEqual(landingLevel(0), GROUND)
    self.assertAlmostEqual(landingLevel(FLIGHTS), FLOOR)
    self.assertLess(math.degrees(math.atan2(rise(), 4.0)), 35.0)
    for k in range(FLIGHTS - 1):
      _, (_, end), (_, high) = flightOf(k)
      _, (start, _), (low, _) = flightOf(k + 1)
      self.assertAlmostEqual(end, start)
      self.assertAlmostEqual(high, low)
    _, (_, end), _ = flightOf(FLIGHTS - 1)
    self.assertGreater(end, STAIR_TOP[0][0] - 1.5)
    self.assertEqual(len(towerSolids()), (STEPS + 1) * FLIGHTS + 1 + 4 + 8)
    self.assertLess(rise() / STEPS, STEP)

  def test_lift(self) -> None:
    """Sent down it rides to the ground (as fast as 'FAST' allows), its
    doors shut on the way and open where it stands."""
    lift = TowerLift()
    self.assertEqual(lift.doors, 4)
    lift.sent(FOOT)
    seconds = 0.0
    while lift.target is not None and seconds < 120.0:
      lift.moved(FRAME)
      seconds += FRAME
      if lift.target is not None:
        self.assertEqual(lift.doors, 0)
    self.assertTrue(lift.atFoot)
    self.assertEqual(lift.doors, 8)
    self.assertLess(seconds, (TOP - FOOT) / FAST + 10.0)

  def test_climb(self) -> None:
    """Up a flight he walks from the ground to the first landing."""
    cockpit, world, meter = self._world()
    crewman = cockpit.crewman
    (y0, y1), (xa, xb), (za, zb) = flightOf(0)
    self._placed(cockpit, (xa - 0.6, 0.5 * (y0 + y1), za), (1.0, 0.0, 0.0))
    self._walked(world, meter, cockpit, set(), 0.3)
    self._walked(world, meter, cockpit, {'ahead'}, 3.0)
    self.assertGreater(crewman.soles()[2], zb - 0.2, crewman.middle)

  def test_ride(self) -> None:
    """Standing in the car at the hall, sent down, he rides it to the
    ground, standing on its floor, unhurt."""
    cockpit, world, meter = self._world()
    crewman = cockpit.crewman
    lift = TowerLift()
    (x0, y0, _), (x1, y1, _) = SHAFT
    self._placed(cockpit, (0.5 * (x0 + x1), 0.5 * (y0 + y1), TOP),
                 (1.0, 0.0, 0.0))
    world.stationed(False, (), towerSolids() + lift.boxesOf())
    self._walked(world, meter, cockpit, set(), 0.3)
    self.assertTrue(lift.holds(crewman.middle))
    lift.sent(FOOT)
    for _ in range(int(30.0 / FRAME)):
      lift.moved(FRAME)
      world.walked(1 | lift.doors)
      world.stationed(False, (), towerSolids() + lift.boxesOf())
      self._walked(world, meter, cockpit, set(), FRAME)
    self.assertTrue(lift.atFoot)
    self.assertLess(abs(crewman.soles()[2] - FOOT), 0.05)
    self.assertLess(world.landed, 3.0)

  def _world(self) -> tuple:
    """Returns his cockpit (him up), the cabin's world with the tower's
    rooms and solids, and the felt pull of the pad (one g)."""
    cockpit, meter = Cockpit(), Accelerometer()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    world.walked(1)
    world.stationed(False, (), towerSolids())
    return cockpit, world, meter

  def _placed(self, cockpit: Cockpit, soles: tuple, facing: tuple) -> None:
    """Puts him standing on 'soles', facing 'facing'."""
    crewman = cockpit.crewman
    crewman.placed((soles[0], soles[1], soles[2] + 0.002 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), facing
    cockpit.yaw, cockpit.pitch = 0.0, 0.0

  def _walked(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, held: set, seconds: float) -> None:
    """Walks him 'seconds' s a frame at a time, the keys 'held'."""
    crewman = cockpit.crewman
    for _ in range(max(1, int(round(seconds / FRAME)))):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      crewman.righted(pull, FRAME)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0), 0))

  def test_enter_lift(self) -> None:
    """From the hall he walks into the lift's car through its door (user,
    2026-11-17: "we need to be more forgiving about how much space Asger
    needs. Just now, I couldn't go into the elevator"), and the stairs'
    doorway too, at an angle."""
    lift = TowerLift()
    for start, facing, inside in (
        ((-17.0, 1.5, FLOOR), (-1.0, 0.0, 0.0), lift.holds),
        ((-16.8, 0.6, FLOOR), (-0.92, -0.39, 0.0),
         lambda p: p[0] < -19.0)):
      cockpit, world, meter = self._world()
      world.walked(1 | lift.doors)
      world.stationed(False, (), towerSolids() + lift.boxesOf())
      self._placed(cockpit, start, facing)
      self._walked(world, meter, cockpit, set(), 0.3)
      self._walked(world, meter, cockpit, {'ahead'}, 1.6)
      self.assertTrue(inside(cockpit.crewman.middle),
                      (start, cockpit.crewman.middle))
