"""
TestBolts covers the magic bolts and the gravity gun aiming at them
(user, 2026-11-17: "Let the space station and the rocket have a few
clearly marked 'magic' bolts in the walls floors and ceilings. The
gravity gun can pull Asger towards them"): each on the cabin's floor,
ceiling or wall facing into the room, where it holds him inside the
cabin clear of every solid; the gun points at one he looks at, never
from his chair, never one facing away; the space station's bolts, docked
(user, 2026-11-17: "use bolts to enter Terra Prime docking"), are on its
rooms' walls and its cages' floors, holding him inside.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._bolts import STATION_BOLTS, holdOf, rocketBolts
from worQt.gaming.space._bolts import stationBolts
from worQt.gaming.space._elevator import Elevator
from worQt.gaming.space._stationinterior import PORT_LOW, roomsInside
from worQt.gaming.space._cabinsolids import solids
from worQt.gaming.space._cockpit import FLOOR, GUN_REACH, NOSE, WALL
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._cockpit import capsuleRadius

from . import SpaceTest


class TestBolts(SpaceTest):
  """Tests for the magic bolts and aiming the gravity gun."""

  def test_placed(self) -> None:
    """Each bolt is on the floor, the ceiling or the wall, facing into
    the room; on the floor, the ceiling and the wall alike."""
    kinds = set()
    for place, way in rocketBolts():
      self.assertAlmostEqual(math.hypot(*way), 1.0, 9)
      if way[2] > 0.99:
        self.assertAlmostEqual(place[2], FLOOR, 9)
        kinds.add('floor')
      elif way[2] < -0.99:
        self.assertAlmostEqual(place[2], NOSE, 9)
        kinds.add('ceiling')
      else:
        across = math.hypot(place[0], place[1])
        self.assertAlmostEqual(across, capsuleRadius(place[2]) - WALL, 9)
        self.assertLess(way[0] * place[0] + way[1] * place[1], 0.0)
        kinds.add('wall')
    self.assertEqual(kinds, {'floor', 'ceiling', 'wall'})

  def test_held(self) -> None:
    """Where the gun holds him is inside the cabin, half a metre and
    more from its wall, floor and ceiling, outside every solid's
    round."""
    for bolt in rocketBolts():
      hold = holdOf(bolt)
      self.assertLess(math.hypot(hold[0], hold[1]),
                      capsuleRadius(hold[2]) - WALL - 0.5)
      self.assertGreater(hold[2], FLOOR + 0.5)
      self.assertLess(hold[2], NOSE - 0.5)
      for middle, half, _ in solids():
        far = math.dist(hold, middle) - math.sqrt(sum(
          h * h for h in half))
        self.assertGreater(far, 0.0, (bolt, middle))

  def test_aimed(self) -> None:
    """Up, looking at a bolt the gun points at it; sitting, at none."""
    cockpit = Cockpit()
    bolts = rocketBolts()
    self.assertIsNone(cockpit.boltAimed(bolts))
    cockpit.gotUp()
    crewman = cockpit.crewman
    soles = crewman.soles()
    for k, (place, way) in enumerate(bolts):
      flat = math.hypot(place[0] - soles[0], place[1] - soles[1])
      if flat < 0.5:
        continue
      crewman.ahead = ((place[0] - soles[0]) / flat,
                       (place[1] - soles[1]) / flat, 0.0)
      off = tuple(p - e for p, e in zip(place, cockpit.eye()))
      far = math.sqrt(sum(x * x for x in off))
      cockpit.yaw, cockpit.pitch = 0.0, math.asin(off[2] / far)
      self.assertEqual(cockpit.boltAimed(bolts), k, (place, far))

  def test_hatch(self) -> None:
    """No magic bolt in the ceiling's hatch (going aboard the station)."""
    from worQt.gaming.space._stationinterior import HATCH
    for place, _ in rocketBolts():
      if abs(place[2] - NOSE) < 1e-9:
        self.assertGreater(math.hypot(place[0], place[1]), HATCH + 0.2)

  def test_beam(self) -> None:
    """The gun's beam (user, 2026-11-17: "a laser beam between it and the
    bolts"): its core runs from the muzzle to the bolt, its grip rings
    the bolt, its coils twist on as time goes; its grab flashes strong
    and settles to one."""
    import numpy
    from worQt.gaming.space._gunbeam import FLASH, GRIP, beamRows
    from worQt.gaming.space._gunbeam import strengthOf
    way = (0.4, -3.0, 1.5)
    core, coils = beamRows(way, 0.0, 1.0)
    reach = numpy.einsum('ij,j->i', core[0][:, :3], numpy.array(way)) / (
      numpy.linalg.norm(way) ** 2)
    self.assertAlmostEqual(float(reach.max()), 1.0, 2)
    self.assertLess(float(reach.min()), 0.01)
    end = numpy.array(way)
    near = numpy.linalg.norm(core[0][:, :3] - end, axis=1)
    self.assertGreater(float(near[near < 2.0 * GRIP].max()), 0.6 * GRIP)
    turned = beamRows(way, 1.0, 1.0)[1]
    self.assertGreater(float(numpy.abs(turned[0][:, :3] - coils[0][:, :3])
                             .max()), 0.01)
    self.assertAlmostEqual(strengthOf(0.0), FLASH, 9)
    self.assertAlmostEqual(strengthOf(5.0), 1.0, 6)
    self.assertGreater(strengthOf(0.1), strengthOf(0.2))

  def test_three(self) -> None:
    """The gun's 3 (user, 2026-11-17: "a more prominent 3 on the side.
    where it is visible"): on its left side (the one his eyes see), off
    it, facing his eyes' side, big."""
    import numpy
    from worQt.gaming.space._dashboard import pieceRows
    from worQt.gaming.space._dashpictures import labelCells
    from worQt.gaming.space._gunmodel import gunParts, sideMark
    rows = numpy.concatenate([part[2][:, :3] for part in gunParts()])
    mark, _ = pieceRows(('gun mark', 0), labelCells())
    self.assertTrue((mark[:, 0] < rows[:, 0].min()).all())
    self.assertTrue((mark[:, 3] < -0.99).all())
    middle, half = sideMark()
    self.assertGreater(middle[0], 0.0)
    self.assertGreater(half, 0.04)

  def test_station(self) -> None:
    """Docked, the station's bolts lie on its rooms' walls (the port's,
    the hub's end round the port) or on its cages' floors, facing into
    them: the gun holds him inside a room, or in the cage; from the
    hatch to a cage each is within the gun's reach of one before it."""
    ways = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0))
    elevators = [Elevator() for _ in ways]
    bolts = stationBolts(ways, tuple(e.floor for e in elevators))
    self.assertEqual(len(bolts), STATION_BOLTS)
    for k, bolt in enumerate(bolts):
      place, way = bolt
      self.assertAlmostEqual(math.hypot(*way), 1.0, 9)
      hold = holdOf(bolt)
      if k < 10:
        self.assertLess(abs(roomsInside(place, True, ways)), 0.01, k)
        self.assertGreater(roomsInside(hold, True, ways), 0.9, k)
      else:
        self.assertTrue(elevators[k - 10].holds(ways[k - 10], hold), k)
    hops = ((bolts[0], bolts[2]), (bolts[2], bolts[6]),
            (bolts[6], bolts[10]))
    for one, two in hops:
      self.assertLess(math.dist(holdOf(one), two[0]), GUN_REACH)
    hatch = (0.0, 0.0, PORT_LOW)
    self.assertLess(math.dist(hatch, bolts[0][0]), GUN_REACH)

  def test_picked(self) -> None:
    """The gun picks up its bolt once he is near where it holds him
    (user, 2026-11-17: "right click pulls Asger towards it, but only as
    long as Asger holds right click *or* Asger gets close enough to it
    to "pick" up the bolt"): from then on he holds on; let go, not."""
    from worQt.gaming.space._crewman import PICKED_UP, Crewman
    crewman = Crewman()
    crewman.unbuckled()
    bolt = rocketBolts()[0]
    hold = holdOf(bolt)
    crewman.towed(0, hold)
    crewman.middle = tuple(h + 1.0 for h in hold)
    self.assertFalse(crewman.picked())
    self.assertFalse(crewman.attached)
    crewman.middle = tuple(h + 0.5 * PICKED_UP for h in hold[:1]) + hold[1:]
    self.assertTrue(crewman.picked())
    self.assertTrue(crewman.attached)
    self.assertFalse(crewman.picked())
    crewman.letGo()
    self.assertFalse(crewman.attached)
    self.assertIsNone(crewman.towTo)

  def test_walls(self) -> None:
    """The gun takes no bolt through a wall (user, 2026-11-17: "the
    gravgun should not be able to grab bolts through walls"): one beyond
    the cabin's wall, facing him, is aimed at only if nothing is in the
    way."""
    from worQt.gaming.space._cockpit import inCabin
    from worQt.gaming.space._crewman import MIDDLE
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    crewman.placed((-3.0, 0.0, FLOOR + 0.002 + MIDDLE), (0.0, 0.0, 0.0), 0,
                   (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0)
    eye = cockpit.eye()
    bolt = ((-7.0, 0.0, eye[2]), (1.0, 0.0, 0.0))
    cockpit.yaw, cockpit.pitch = 0.0, 0.0
    self.assertEqual(cockpit.boltAimed((bolt,)), 0)
    self.assertIsNone(cockpit.boltAimed((bolt,), inCabin))
    inside = ((-4.0, 0.0, eye[2]), (1.0, 0.0, 0.0))
    self.assertEqual(cockpit.boltAimed((inside,), inCabin), 0)
