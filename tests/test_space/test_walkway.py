"""
TestWalkway covers the way into the rocket on the pad (user,
2026-11-17: "let's have an entrance ot the rocket perpendicular to the
way Asger faces, but behind him and behind where all those books were
at"; "The door out of the rocket should be connected to a retractable
walk way. Here the quest begins"; "Asger must start outside in the
night where we can reasonably spot Terra Prime from the ground"): the
door is cut through both walls; dismissed, the walkway goes, clear of
the hull all the way (user: "geometric collision between rocket and
walk way"); the walkway's rooms and the doorway join the cabin's; Asger
stands in the tower's hall, walks the walkway to the shut door (its
leaf in the way: '_door', 'test_door') and no further, and through it
open into the cabin; the door's key outside is worked from
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
from worQt.gaming.space._turns import dot, rotated, unit
from worQt.gaming.space._vessel import LEGS, Vessel
from worQt.gaming.space._walkway import DOOR_HIGH, DOOR_SPAN
from worQt.gaming.space._launchtower import START, groundsInside
from worQt.gaming.space._launchtower import towerSolids
from worQt.gaming.space._walkway import SECTION_LONG, Walkway
from worQt.gaming.space._door import TRAVEL, Door
from worQt.gaming.space._walkway import doorwayInside, walkwayInside
from worQt.gaming.space._walkwaymeshes import outsideKey
from worQt.gaming.space._vessel import RADIUS

from . import FRAME, SpaceTest


class TestWalkway(SpaceTest):
  """Tests for the walkway, the door and the quest."""

  #  The cabin's kernels step on the CPU here: minutes, not half one.
  __time_out__ = 900.0

  def test_away(self) -> None:
    """At the door its rooms join the cabin's; dismissed (once) it folds
    on its motor, its sections into each other, then swings away on the
    other, and is gone (its rooms with it) within half a minute (user,
    2026-11-18: "harmonica away and turn to a different direction")."""
    walkway = Walkway(True)
    self.assertEqual(walkway.outside, 1)
    self.assertEqual(walkway.dismissed(), '')
    self.assertEqual(walkway.outside, 0)
    self.assertNotEqual(walkway.dismissed(), '')
    folded = None
    for _ in range(int(30.0 / FRAME)):
      walkway.moved(FRAME, 0.0, 0.0)
      if folded is None and walkway.swing > 1e-3:
        folded = walkway.long
      if walkway.away:
        break
    self.assertTrue(walkway.away)
    self.assertLess(abs(folded - SECTION_LONG), 0.01)
    self.assertTrue(Walkway(False).away)

  def test_window(self) -> None:
    """The main door has a window at his eyes (user, 2026-11-18: "Put a
    window in the main door"): within the door, the leaf open there
    (none of its faces across it), its pane filling it in the middle of
    the wall's thickness."""
    from worQt.gaming.space._cockpit import WALL
    from worQt.gaming.space._walkway import DOOR_HIGH, DOOR_SPAN
    from worQt.gaming.space._walkway import DOOR_WINDOW
    from worQt.gaming.space._walkwaymeshes import doorGlassRows, leafRows
    (w0, w1), (low, high) = DOOR_WINDOW
    self.assertLess(DOOR_SPAN[0], w0)
    self.assertLess(w1, DOOR_SPAN[1])
    cockpit = Cockpit()
    cockpit.gotUp()
    eye = cockpit.eye()[2]
    self.assertLess(low, eye)
    self.assertLess(eye, high)
    self.assertLess(high, DOOR_HIGH)
    rows, faces = leafRows()
    for k in range(0, len(faces), 3):
      middle = numpy.mean(rows[faces[k:k + 3], :3], 0)
      angle = math.degrees(math.atan2(middle[1], middle[0])) % 360.0
      inside = (w0 + 0.1 < angle < w1 - 0.1
                and low + 0.01 < middle[2] < high - 0.01)
      self.assertFalse(inside, (angle, middle[2]))
    glass, _ = doorGlassRows()
    angles = numpy.degrees(numpy.arctan2(glass[:, 1], glass[:, 0])) % 360.0
    self.assertAlmostEqual(float(angles.min()), w0, 6)
    self.assertAlmostEqual(float(angles.max()), w1, 6)
    self.assertAlmostEqual(float(glass[:, 2].min()), low, 9)
    self.assertAlmostEqual(float(glass[:, 2].max()), high, 9)
    for row in glass:
      self.assertAlmostEqual(math.hypot(row[0], row[1]), capsuleRadius(
        row[2]) - 0.5 * WALL, 9)

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
    not; the doorway runs through it from the walkway (the two meeting
    a hair past the hull's skin) into the cabin."""
    self.assertGreater(groundsInside((-15.0, 0.0, FLOOR + 1.0), False,
                                     False), 0.9)
    self.assertGreater(walkwayInside((-8.0, 0.0, FLOOR + 1.0)), 0.9)
    wall = (-capsuleRadius(FLOOR + 1.0) + 0.02, 0.0, FLOOR + 1.0)
    self.assertLess(walkwayInside(wall), 0.0)
    self.assertFalse(inCabin(wall))
    self.assertGreater(doorwayInside(wall), 0.3)
    self.assertLess(doorwayInside((-5.4, 0.0, FLOOR + 1.0)), 0.0)
    self.assertGreater(walkwayInside((-5.4, 0.0, FLOOR + 1.0)), 0.1)
    meet = (-5.06, 0.0, FLOOR + 1.0)
    self.assertGreater(min(doorwayInside(meet), walkwayInside(meet)), 0.0)
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
    world.walked(3)
    world.stationed(False, (), towerSolids() + Walkway(True).boxesOf())
    door = Door(False)
    world.doorPlaced(*door.boxOf())
    self._walked(world, meter, cockpit, set(), 0.5)
    self.assertLess(abs(crewman.soles()[2] - FLOOR), 0.02)
    self._walked(world, meter, cockpit, {'ahead'}, 6.0)
    skin = capsuleRadius(FLOOR + 1.0)
    self.assertLess(crewman.middle[0], -skin)
    self.assertGreater(crewman.middle[0], -skin - 0.51)
    door.arc = TRAVEL
    world.doorPlaced(*door.boxOf())
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
    began = now + timedelta(0, _nightStart(now, 'cpu'))
    system = solarSystemOn(julianOf(began), 'cpu')
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
      cockpit.yaw, cockpit.pitch, _ = crewman.righted(
        pull, FRAME, cockpit.yaw, cockpit.pitch)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))

  def test_clear(self) -> None:
    """Out at the door and folding and swinging away, its sections never
    cut into the rocket's hull (at the door a hair off it)."""
    walkway = Walkway(True)
    walkway.dismissed()
    nearest = math.inf
    for _ in range(int(30.0 / FRAME)):
      for middle, half, turn, _ in walkway.boxesOf():
        for sx in (-1.0, 1.0):
          for sy in (-1.0, 1.0):
            for sz in (-1.0, 1.0):
              x, y, z = (m + r for m, r in zip(middle, rotated(turn, (
                sx * half[0], sy * half[1], sz * half[2]))))
              skin = RADIUS if z < FLOOR else capsuleRadius(z)
              nearest = min(nearest, math.hypot(x, y) - skin)
      if walkway.away:
        break
      walkway.moved(FRAME, 0.0, 0.0)
    self.assertGreater(nearest, 0.0)
    self.assertLess(nearest, 0.2)

  def test_dismissed_furnished(self) -> None:
    """With Asger in his chair and the door locked, the window sends the
    walkway away though the deck's furnishings, loose things of the
    cabin's world, are out on Terra Prime (user, 2026-11-19: "i can't
    dismiss the walkway": they were counted as out on the walkway); and
    docked they never keep the rocket at the station."""
    from types import SimpleNamespace

    from worQt.gaming.space._deckthings import TELEPORTED, DeckThings
    from worQt.gaming.space._deckthings import deckThings
    from worQt.gaming.space._deckthings import deckWorldThings
    from worQt.gaming.space._furnishings import looseThings
    from worQt.gaming.space._spacewindow import SpaceWindow
    world = CabinWorld('cpu', looseThings() + deckWorldThings())
    world.bodiesPlaced(len(looseThings()), DeckThings().laid(TELEPORTED),
                       (0.0,) * len(deckThings()))
    told = []
    window = SimpleNamespace(
      cockpit=Cockpit(), world=world, door=SimpleNamespace(locked=True),
      walkway=SimpleNamespace(dismissed=lambda: told.append('away') or ''),
      _noteOf=told.append, shaftDoors=(),
      vessel=SimpleNamespace(docked=True))
    window._cabinLoose = lambda: SpaceWindow._cabinLoose(window)
    self.assertTrue(world.shown())
    self.assertTrue(any(not inCabin(place) for place, _ in world.shown()))
    SpaceWindow._dismissed(window)
    self.assertEqual(told[0], 'away', told)
    self.assertEqual(SpaceWindow._aboardWhy(window), '')
