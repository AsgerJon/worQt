"""
TestAboard covers Asger going up the rocket and aboard the space station
(user, 2026-11-17: "all aboard Asger's kolonihave i rummet!"; 2026-11-19:
the rocket's three levels, its head in Terra Prime's drum, its top
floor's four doors facing the four shafts): the levels and the hatches
between them are rooms always; docked the top floor's doorways, the
shafts and the ring join them; he floats up the axis through the
hatches; docked he floats out of the top floor through a door into the
cage at its stop by the drum (undocked the wall stops him), a door's
shut leaf stops him; on the ring's deck the station's turn alone pulls
one g, and he stands; the spoke's elevator carries him out, and stops
with its floor in the deck, its sides along the ring open.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._elevator import ACCEL, AWAY, CAR_HIGH, DECK_STOP
from worQt.gaming.space._elevator import HUB_STOP, Elevator
from worQt.gaming.space._levels import CEILING, HEAD, LEVELS, ROOF
from worQt.gaming.space._shaftdoor import ShaftDoor
from worQt.gaming.space._station import SPIN
from worQt.gaming.space._stationinterior import DECK, PLANE, roomOf
from worQt.gaming.space._stationinterior import roomsInside, shaftWays
from worQt.gaming.space._stationinterior import stationWay
from worQt.gaming.space._terminal import LANDING, terminalSolids

from . import FRAME, SpaceTest

#  The docked rocket's own axes in the station's: its nose down the
#  station's axis, unrolled.
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
#  The station's own z in the docked rocket's axes; a cage's inside
#  reaches this far past its plates (as the window has it), m.
AXIAL = stationWay((0.0, 0.0, 1.0), RELATIVE)
CAGE_OVER = 0.3
#  Asger's legs at rest.
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0))


class TestAboard(SpaceTest):
  """Tests for going aboard the space station."""

  #  The cabin's kernels on the CPU: some 6 s a second of its world.
  __time_out__ = 900.0

  def _docked(self, docked: bool) -> tuple:
    """Returns the cabin's world (docked or not), an accelerometer
    turning with the station, the shafts' ways and their elevators."""
    world = CabinWorld('cpu')
    ways = shaftWays(RELATIVE)
    elevators = [Elevator() for _ in ways]
    self._sent(world, docked, ways, elevators)
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    return world, meter, ways, elevators

  def _sent(self, world: CabinWorld, docked: bool, ways: tuple,
            elevators: list, doors: tuple = ()) -> None:
    """Puts every elevator's plates, the leaves of 'doors' (the top
    floor's) and the terminals' solids in 'world', each cage's inside a
    room where it is."""
    boxes = tuple(box for elevator, way in zip(elevators, ways)
                  for box in elevator.boxesOf(way, AXIAL)) + tuple(
      door.boxOf() for door in doors) + terminalSolids(RELATIVE)
    world.stationed(docked, ways, boxes, _cagesOf(elevators))

  def _up(self, middle: tuple, velocity: tuple, up: tuple) -> Cockpit:
    """Returns a cockpit, Asger up out of his chair at 'middle' moving
    'velocity', his up 'up'."""
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    crewman.placed(middle, velocity, 0, (0.0, 0.0, 0.0))
    crewman.up = up
    return cockpit

  def _flown(self, world: CabinWorld, meter: Accelerometer,
             cockpit: Cockpit, seconds: float, ways: tuple,
             elevators: list) -> None:
    """Steps 'world' 'seconds' s a frame at a time, Asger righted by the
    pull where he is, the elevators moving."""
    crewman = cockpit.crewman
    for _ in range(int(round(seconds / FRAME))):
      crewman.righted(meter.pullAt(crewman.middle, crewman.velocity),
                      FRAME)
      if elevators:
        self._sent(world, True, ways, elevators)
      for elevator in elevators:
        elevator.moved(FRAME)
      world.stepped(FRAME, meter, crewman, STILL)

  def test_rooms(self) -> None:
    """The levels and the hatches are rooms docked or not, the roof and
    the head's wall not; docked the top floor's doorways, a cage's inside
    where it is (the rest of its shaft is vacuum: user, 2026-11-19, "the
    spokes are not pressurized") and the ring join them (beside a door
    the wall stays a wall); on the
    deck the station's turn alone pulls one g, outward; on the top floor
    next to nothing."""
    ways = shaftWays(RELATIVE)
    hub = tuple(_cagesOf([Elevator()]) * 4)
    cages = ((398.0, 402.0),) + hub[1:]
    for docked in (False, True):
      for point in ((1.0, 0.0, CEILING - 1.0),
                    (1.0, 0.0, LEVELS[1][0] + 1.0),
                    (0.0, 0.3, CEILING + 0.1), (2.0, 2.0, PLANE)):
        self.assertGreater(roomsInside(point, docked, ways, cages), 0.0,
                           point)
      for point in ((0.0, 0.0, ROOF + 0.1), (3.0, 3.0, PLANE),
                    (1.5, 0.0, CEILING + 0.1)):
        self.assertLess(roomsInside(point, docked, ways, cages), 0.0, point)
    out = (HEAD + 0.2, 0.0, PLANE)
    self.assertLess(roomsInside(out, False, ways, cages), 0.0)
    self.assertGreater(roomsInside(out, True, ways, cages), 0.0)
    for point, room in (((1.0, 0.0, CEILING - 1.0), 'cabin'),
                        ((1.0, 0.0, LEVELS[1][0] + 1.0), 'level 1'),
                        ((1.0, 0.0, PLANE), 'level 2'),
                        ((0.0, 0.3, CEILING + 0.1), 'hatch'),
                        ((HEAD + 0.2, 0.0, PLANE), 'doorway'),
                        ((400.0, 0.0, PLANE), 'shaft'),
                        ((DECK - 3.0, 50.0, PLANE + 5.0), 'ring')):
      self.assertEqual(roomOf(point, ways, cages), room, point)
    self.assertLess(roomsInside((DECK + 0.5, 0.0, PLANE), True, ways,
                                cages), 0.0)
    self.assertLess(roomsInside((200.0, 0.0, PLANE), True, ways, cages),
                    0.0)
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    pull = meter.pullAt((DECK, 0.0, PLANE), (0.0, 0.0, 0.0))
    self.assertAlmostEqual(pull[0], G0, 6)
    middle = meter.pullAt((2.0, 0.0, PLANE), (0.0, 0.0, 0.0))
    self.assertLess(math.hypot(*middle), 0.01 * G0)

  def test_way_up(self) -> None:
    """The way up beside the pole from the cabin's floor through both
    hatches to the top floor's ceiling is a room all along, never
    shallower than his box's half width near the axis (rooms meeting at
    a plane are nought deep there: his box stopped dead under the hub's
    mouth, the user's let's play, 2026-11-18)."""
    from worQt.gaming.space._crewman import WIDE
    ways = shaftWays(RELATIVE)
    z = LEVELS[0][0] + 0.5
    while z < LEVELS[2][1] - 0.5:
      for x, y in ((0.3, 0.0), (0.0, -0.3), (-0.25, 0.1)):
        for docked in (False, True):
          self.assertGreater(roomsInside((x, y, z), docked, ways, ()),
                             0.5 * WIDE, (x, y, z))
      z += 0.05

  def test_hatch(self) -> None:
    """Floating up at 1 m/s beside the pole under the cabin's hatch, he
    goes through both hatches up to the top floor (docked or not)."""
    for docked in (True, False):
      world, meter, ways, _ = self._docked(docked)
      cockpit = self._up((0.3, 0.0, CEILING - 1.3), (0.0, 0.0, 1.0),
                         (0.0, 0.0, 1.0))
      self._flown(world, meter, cockpit, 7.0, ways, [])
      z = cockpit.crewman.middle[2]
      self.assertGreater(z, LEVELS[2][0] + 0.5, docked)
      self.assertLess(z, LEVELS[2][1], docked)

  def test_doorway(self) -> None:
    """Floating out of the top floor at 1 m/s straight at door nought from
    a metre before it (further, the station's turn bends a float past the
    door: honest): docked, its leaf open, he passes the door and the gap
    into the cage at its stop by the drum; its leaf shut, it stops him;
    undocked the wall does."""
    for docked, opened in ((True, True), (True, False), (False, True)):
      world, meter, ways, elevators = self._docked(docked)
      door = ShaftDoor(0)
      if opened:
        door.opened(True)
        door.moved(10.0, 0.0, 0.0)
      if docked:
        self._sent(world, True, ways, elevators, (door,))
      cockpit = self._up((HEAD - 1.0, 0.0, PLANE), (1.0, 0.0, 0.0),
                         (0.0, 0.0, 1.0))
      self._flown(world, meter, cockpit, 4.0, ways, [])
      crewman = cockpit.crewman
      inCage = elevators[0].holds(ways[0], crewman.middle)
      self.assertEqual(inCage, docked and opened, (docked, opened,
                                                   crewman.middle))
      if not inCage:
        self.assertLess(crewman.middle[0], HEAD, (docked, opened))

  def test_deck(self) -> None:
    """On the ring's deck, between the spokes, the station's turn stands
    him on it (his soles within 3 cm of it), touching."""
    world, meter, ways, _ = self._docked(True)
    way = (math.sqrt(0.5), math.sqrt(0.5), 0.0)
    middle = tuple((DECK - 0.95) * w for w in way[:2]) + (PLANE,)
    cockpit = self._up(middle, (0.0, 0.0, 0.0), tuple(-w for w in way))
    self._flown(world, meter, cockpit, 2.0, ways, [])
    crewman = cockpit.crewman
    soles = crewman.soles()
    self.assertLess(abs(math.hypot(soles[0], soles[1]) - DECK), 0.03)
    self.assertTrue(crewman.touches)

  def test_ride_out(self) -> None:
    """Floating in the cage at the hub's stop, the cage called, it
    carries him out with it (the roof closed over him), not leaving him
    behind."""
    world, meter, ways, elevators = self._docked(True)
    way = ways[0]
    start = HUB_STOP - 1.5
    middle = (start * way[0], start * way[1], PLANE)
    cockpit = self._up(middle, (0.0, 0.0, 0.0), tuple(-w for w in way))
    elevators[0].called()
    self._flown(world, meter, cockpit, 6.0, ways, elevators)
    car = elevators[0]
    out = sum(m * w for m, w in zip(cockpit.crewman.middle, way))
    self.assertGreater(car.floor, HUB_STOP + 20.0)
    self.assertGreater(out, car.floor - CAR_HIGH)
    self.assertLess(out, car.floor)

  def test_ride_in(self) -> None:
    """Standing in the cage as it slows to the terminal's landing, he
    stands on its floor at the landing when it stops, and its side
    toward the platform is open (the other shut)."""
    world, meter, ways, elevators = self._docked(True)
    car, way = elevators[0], ways[0]
    car.floor = DECK_STOP - 30.0
    car.speed = math.sqrt(2.0 * ACCEL * 30.0)
    car.target = DECK_STOP
    self._sent(world, True, ways, elevators)
    middle = tuple((car.floor - 0.95) * w for w in way[:2]) + (PLANE,)
    cockpit = self._up(middle, tuple(car.speed * w for w in way),
                       tuple(-w for w in way))
    self._flown(world, meter, cockpit, 6.0, ways, elevators)
    self.assertTrue(car.atDeck)
    soles = cockpit.crewman.soles()
    self.assertLess(abs(math.hypot(soles[0], soles[1]) - LANDING), 0.05)
    boxes = car.boxesOf(way, AXIAL)
    self.assertEqual(boxes[2][0], AWAY)
    self.assertNotEqual(boxes[3][0], AWAY)


def _cagesOf(elevators: list) -> tuple:
  """Returns each elevator's cage's inside along its shaft (from, to)."""
  return tuple((e.floor - CAR_HIGH - CAGE_OVER, e.floor + CAGE_OVER)
               for e in elevators)
