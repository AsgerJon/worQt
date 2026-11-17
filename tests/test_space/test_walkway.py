"""
TestWalkway covers the way into the rocket on the pad (user,
2026-11-17: "let's have an entrance ot the rocket perpendicular to the
way Asger faces, but behind him and behind where all those books were
at"; "The door out of the rocket should be connected to a retractable
walk way. Here the quest begins"; "Asger must start outside in the
night where we can reasonably spot Terra Prime from the ground"): the
door is cut through both walls; it opens only unlocked with the walkway
there, locks only shut, the walkway goes only with the door locked,
clear of the hull all the way (user: "geometric collision between
rocket and walk way");
the walkway's rooms and the doorway join the cabin's; Asger stands in
the tower's hall, walks the walkway to the shut door and no further, and
through it open into the cabin; the door's key outside is worked from
outside, its keys inside from inside; the quest ticks off its steps;
the game starts at night with Terra Prime high over the pad.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import numpy

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabin import capsuleShell
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import FLOOR, Cockpit, capsuleRadius
from worQt.gaming.space._cockpit import inCabin
from worQt.gaming.space._crewman import MIDDLE
from worQt.gaming.space._night import isDark
from worQt.gaming.space._planets import PAD, julianOf, solarSystemOn
from worQt.gaming.space._quest import STEPS, Quest
from worQt.gaming.space._spacewindow import RISEN, _nightStart
from worQt.gaming.space._station import Station
from worQt.gaming.space._turns import dot, unit
from worQt.gaming.space._vessel import LEGS, Vessel
from worQt.gaming.space._walkway import DOOR_HIGH, DOOR_SPAN
from worQt.gaming.space._launchtower import START, groundsInside
from worQt.gaming.space._launchtower import towerSolids
from worQt.gaming.space._walkway import SLIDE, SWING_AWAY, Walkway
from worQt.gaming.space._walkway import doorwayInside, walkwayInside
from worQt.gaming.space._walkwaymeshes import armParts, armPivot
from worQt.gaming.space._walkwaymeshes import outsideKey
from worQt.gaming.space._vessel import RADIUS
from worQt.gaming.space._walkway import PAD_UP

from . import FRAME, SpaceTest


class TestWalkway(SpaceTest):
  """Tests for the walkway, the door and the quest."""

  #  The cabin's kernels step on the CPU here: minutes, not half one.
  __time_out__ = 900.0

  def test_door(self) -> None:
    """Open, it slides fully open over 'SLIDE' s; it shuts; it locks
    only shut; locked it will not open; the walkway goes only with the
    door locked, swings away and is gone (no door then)."""
    walkway = Walkway(True)
    self.assertEqual(walkway.outside, 1)
    self.assertEqual(walkway.dismissed(), 'lock the door first')
    self.assertEqual(walkway.opened(), '')
    walkway.moved(0.5 * SLIDE)
    self.assertFalse(walkway.passable)
    walkway.moved(0.6 * SLIDE)
    self.assertTrue(walkway.passable)
    self.assertEqual(walkway.outside, 3)
    self.assertEqual(walkway.locking(), 'close the door first')
    self.assertEqual(walkway.closed(), '')
    walkway.moved(SLIDE)
    self.assertTrue(walkway.shut)
    self.assertEqual(walkway.locking(), '')
    self.assertEqual(walkway.opened(), 'the door is locked')
    self.assertEqual(walkway.dismissed(), '')
    self.assertEqual(walkway.outside, 0)
    walkway.moved(SWING_AWAY / math.radians(12.0) + 5.0)
    self.assertTrue(walkway.away)
    self.assertNotEqual(walkway.locking(), '')
    self.assertTrue(Walkway(False).away)

  def test_cut(self) -> None:
    """No face of either wall lies in the door's opening (behind him,
    from the floor up)."""
    for inner in (True, False):
      rows = numpy.asarray(capsuleShell(inner)[0])
      angle = numpy.degrees(numpy.arctan2(rows[:, 1], rows[:, 0])) % 360.0
      z = rows[:, 2]
      inside = ((angle > DOOR_SPAN[0] + 0.5) & (angle < DOOR_SPAN[1] - 0.5)
                & (z > FLOOR + 0.05) & (z < DOOR_HIGH - 0.05))
      self.assertFalse(inside.any(), inner)

  def test_rooms(self) -> None:
    """The tower's hall and the walkway are rooms, the hull's wall is
    not; the doorway runs through it from the walkway into the
    cabin."""
    self.assertGreater(groundsInside((-15.0, 0.0, FLOOR + 1.0), False,
                                     False), 0.9)
    self.assertGreater(walkwayInside((-8.0, 0.0, FLOOR + 1.0)), 0.9)
    wall = (-capsuleRadius(FLOOR + 1.0) + 0.02, 0.0, FLOOR + 1.0)
    self.assertLess(walkwayInside(wall), 0.0)
    self.assertFalse(inCabin(wall))
    self.assertGreater(doorwayInside(wall), 0.3)
    self.assertGreater(doorwayInside((-5.4, 0.0, FLOOR + 1.0)), 0.1)
    self.assertTrue(inCabin((-4.6, 0.0, FLOOR + 1.0)))
    self.assertGreater(doorwayInside((-4.6, 0.0, FLOOR + 1.0)), 0.3)

  def test_walk_in(self) -> None:
    """In the tower's hall he stands where he starts; walking ahead
    along the walkway he stops at the shut door; it open, he walks on
    into the cabin."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    crewman = cockpit.crewman
    soles = START[0]
    crewman.placed((soles[0], 0.0, soles[2] + MIDDLE), (0.0, 0.0, 0.0), 0,
                   (0.0, 0.0, 0.0))
    world.walked(1)
    world.stationed(False, (), towerSolids())
    self._walked(world, meter, cockpit, set(), 0.5)
    self.assertLess(abs(crewman.soles()[2] - FLOOR), 0.02)
    self._walked(world, meter, cockpit, {'ahead'}, 6.0)
    skin = capsuleRadius(FLOOR + 1.0)
    self.assertLess(crewman.middle[0], -skin)
    self.assertGreater(crewman.middle[0], -skin - 0.5)
    world.walked(3)
    self._walked(world, meter, cockpit, {'ahead'}, 1.5)
    self.assertTrue(inCabin(crewman.middle), crewman.middle)
    self.assertLess(abs(crewman.soles()[2] - FLOOR), 0.02)

  def test_keys(self) -> None:
    """In the walkway before the door's key he is offered it; inside
    the cabin not (the wall between)."""
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    key = outsideKey()[0]
    for x, offered in ((key[0], True), (-4.0, False)):
      crewman.placed((x, 0.2, FLOOR + 0.002 + MIDDLE), (0.0, 0.0, 0.0), 0,
                     (0.0, 0.0, 0.0))
      flat = unit((key[0] - x, key[1] - 0.2, 0.0))
      crewman.up, crewman.ahead = (0.0, 0.0, 1.0), flat
      cockpit.yaw = 0.0
      way = unit(tuple(k - e for k, e in zip(key, cockpit.eye())))
      cockpit.pitch = math.asin(way[2])
      looked = cockpit.lookedAt()
      action = looked.action if looked is not None else ''
      self.assertEqual(action == 'door outside', offered, (x, action))

  def test_quest(self) -> None:
    """Its steps tick off once each; eating and the sofa make one step;
    the current step is the first not done that may not be left out."""
    quest = Quest()
    self.assertEqual(quest.current, 'aboard')
    self.assertTrue(quest.ticked('aboard'))
    self.assertFalse(quest.ticked('aboard'))
    self.assertFalse(quest.ticked('ate'))
    self.assertTrue(quest.ticked('lounged'))
    self.assertIn('rested', quest.done)
    self.assertEqual(quest.current, 'locked')
    for name, _, optional in STEPS:
      if not optional:
        quest.ticked(name)
    self.assertTrue(quest.finished)
    rows = quest.rows()
    self.assertEqual(len(rows), len(STEPS))
    self.assertTrue(rows[0]['text'].startswith('1. '))
    self.assertTrue(rows[6]['optional'])
    with self.assertRaises(KeyError):
      quest.ticked('nonsense')

  def test_night_start(self) -> None:
    """Started outside, it is night on the pad, and Terra Prime is high
    over it at once and overhead a minute on."""
    now = datetime(2026, 11, 17, 6, 20, tzinfo=timezone.utc)
    began = now + timedelta(0, _nightStart(now))
    system = solarSystemOn(julianOf(began))
    terra = system.named('Terra')
    pad = Vessel()
    pad.stood(system, terra, PAD[0], PAD[1], 0.0)
    pad.touching = len(LEGS)
    self.assertTrue(isDark(system, pad, 0.0))
    station = Station(system, -RISEN)
    heights = []
    for t in (0.0, 60.0):
      if t:
        pad.carried(system, t)
      there = station.stateAt(t)[0]
      way = unit(tuple(s - p for s, p in zip(there, pad.place)))
      heights.append(math.degrees(math.asin(dot(way, unit(pad.place)))))
    self.assertGreater(heights[0], 30.0)
    self.assertGreater(heights[1], 75.0)

  def _walked(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, held: set, seconds: float) -> None:
    """Walks him 'seconds' s a frame at a time, the keys 'held'."""
    crewman = cockpit.crewman
    for _ in range(int(round(seconds / FRAME))):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      crewman.righted(pull, FRAME)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))

  def test_clear(self) -> None:
    """Dismissed, the walkway slides back and swings away without ever
    cutting into the rocket's hull (at the door a hair off it)."""
    rows = numpy.concatenate([part[:, :3] for part, _ in
                              armParts().values()])
    walkway = Walkway(True)
    walkway.opened()
    walkway.closed()
    walkway.locking()
    walkway.dismissed()
    nearest = math.inf
    while not walkway.away:
      a = walkway.swing
      c, s = math.cos(a), math.sin(a)
      local = rows[:, 0] - walkway.back
      x = armPivot()[0] + c * local - s * rows[:, 1]
      y = armPivot()[1] + s * local + c * rows[:, 1]
      z = armPivot()[2] + rows[:, 2] - PAD_UP
      skin = numpy.where(z < FLOOR, RADIUS, numpy.vectorize(
        capsuleRadius)(z))
      nearest = min(nearest, float((numpy.hypot(x, y) - skin).min()))
      walkway.moved(0.05)
    self.assertGreater(nearest, 0.05)
