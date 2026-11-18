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
    the hub's end round the port), float in the hub's middle and in each
    spoke's mouth (user, 2026-11-18), or lie on its cages' floors, facing
    whence they are reached: the gun holds him inside a room, or in the
    cage."""
    ways = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0))
    elevators = [Elevator() for _ in ways]
    bolts = stationBolts(ways, tuple(e.floor for e in elevators))
    self.assertEqual(len(bolts), STATION_BOLTS)
    for k, bolt in enumerate(bolts):
      place, way = bolt
      self.assertAlmostEqual(math.hypot(*way), 1.0, 9)
      hold = holdOf(bolt)
      if k < 6:
        self.assertLess(abs(roomsInside(place, True, ways)), 0.01, k)
      elif k < 11:
        self.assertGreater(roomsInside(place, True, ways), 3.0, k)
      if k < 11:
        self.assertGreater(roomsInside(hold, True, ways), 0.9, k)
      else:
        self.assertTrue(elevators[k - 11].holds(ways[k - 11], hold), k)

  def test_way_in(self) -> None:
    """Docked, the way in (user, 2026-11-18: "a bolt floating in the very
    center of the docking chamber on the Terra Prime side so you can
    pull yourself in. Then each of the four arms to the outer ring has a
    dedicated bolt that can be reach from the center"): from the
    cabin's floor under the hatch the hub's middle bolt, from where it
    holds him each spoke's mouth's, from where that holds him its cage's
    floor's: each within the gun's reach, facing him and in sight (the
    rooms walked, the cages' plates met)."""
    import numpy
    from worQt.gaming.space._sight import inSight
    ways = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (-1.0, 0.0, 0.0),
            (0.0, -1.0, 0.0))
    elevators = [Elevator() for _ in ways]
    bolts = stationBolts(ways, tuple(e.floor for e in elevators))
    plates = [box for e, way in zip(elevators, ways)
              for box in e.boxesOf(way)]
    middles = numpy.array([m for m, _, _, _ in plates], numpy.float64)
    halves = numpy.array([h for _, h, _, _ in plates], numpy.float64)
    axes = []
    for _, _, (w, x, y, z), _ in plates:
      axes.append(numpy.array([
        (1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
         2 * (x * z + w * y)),
        (2 * (x * y + w * z), 1 - 2 * (x * x + z * z),
         2 * (y * z - w * x)),
        (2 * (x * z - w * y), 2 * (y * z + w * x),
         1 - 2 * (x * x + y * y))]))
    keep = middles[:, 2] > -1e3
    boxes = middles[keep], halves[keep], numpy.array(axes)[keep]

    def reached(eye: tuple, bolt: tuple) -> None:
      place, way = bolt
      off = tuple(p - e for p, e in zip(place, eye))
      self.assertLess(math.hypot(*off), GUN_REACH, (eye, place))
      self.assertLess(sum(w * o for w, o in zip(way, off)), 0.0)
      self.assertTrue(inSight(eye, place, lambda point: roomsInside(
        point, True, ways), boxes), (eye, place))

    middle = bolts[6]
    reached((0.0, 0.0, FLOOR + 1.7), middle)
    for k in range(4):
      arm, cage = bolts[7 + k], bolts[11 + k]
      reached(holdOf(middle), arm)
      reached(holdOf(arm), cage)

  def test_walls(self) -> None:
    """The gun takes no bolt through a wall (user, 2026-11-17: "the
    gravgun should not be able to grab bolts through walls"): one beyond
    the cabin's wall, facing him, is aimed at only if nothing is in the
    way."""
    import numpy
    from worQt.gaming.space._crewman import MIDDLE
    from worQt.gaming.space._sight import inSight
    from worQt.gaming.space._stationinterior import cabinInside
    nothing = (numpy.zeros((0, 3)), numpy.zeros((0, 3)),
               numpy.zeros((0, 3, 3)))

    def seen(eye: tuple, there: tuple) -> bool:
      """The cabin alone, no solids."""
      return inSight(eye, there, cabinInside, nothing)

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
    self.assertIsNone(cockpit.boltAimed((bolt,), seen))
    inside = ((-4.0, 0.0, eye[2]), (1.0, 0.0, 0.0))
    self.assertEqual(cockpit.boltAimed((inside,), seen), 0)
