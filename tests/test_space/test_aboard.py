"""
TestAboard covers Asger going aboard the space station (user, 2026-11-17:
"all aboard Asger's kolonihave i rummet!"): docked, the station's rooms
join the cabin's (the hatch through the nose open; undocked, the ceiling
closed); he floats up through the hatch into the port and the hub; on
the ring's deck the station's turn alone pulls one g, and he stands;
the spoke's elevator carries him out from the hub, and stops with its
floor in the deck, its sides along the ring open.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import NOSE, Cockpit
from worQt.gaming.space._elevator import ACCEL, AWAY, CAR_HIGH, DECK_STOP
from worQt.gaming.space._elevator import HUB_STOP, Elevator
from worQt.gaming.space._station import SPIN
from worQt.gaming.space._stationinterior import DECK, PLANE, roomOf
from worQt.gaming.space._stationinterior import roomsInside, shaftWays

from . import FRAME, SpaceTest

#  The docked rocket's own axes in the station's: its nose down the
#  station's axis, unrolled.
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
#  Asger's legs at rest.
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0), 0)


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
    world.stationed(docked, ways, self._boxes(elevators, ways))
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    return world, meter, ways, elevators

  def _boxes(self, elevators: list, ways: tuple) -> tuple:
    """Returns every elevator's plates."""
    return tuple(box for elevator, way in zip(elevators, ways)
                 for box in elevator.boxesOf(way))

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
        world.stationed(True, ways, self._boxes(elevators, ways))
      for elevator in elevators:
        elevator.moved(FRAME)
      world.stepped(FRAME, meter, crewman, STILL)

  def test_rooms(self) -> None:
    """Undocked the cabin's ceiling is closed; docked the hatch opens it
    into the port, the hub, the shafts and the ring; on the deck the
    station's turn alone pulls one g, outward; in the hub next to
    nothing."""
    ways = shaftWays(RELATIVE)
    over = (0.0, 0.0, NOSE + 0.5)
    self.assertLess(roomsInside(over, False, ways), 0.0)
    self.assertGreater(roomsInside(over, True, ways), 0.0)
    for point, room in (((0.0, 0.0, NOSE - 2.0), 'cabin'),
                        ((0.0, 0.0, 45.0), 'port'),
                        ((10.0, 0.0, 100.0), 'hub'),
                        ((400.0, 0.0, PLANE), 'shaft'),
                        ((DECK - 3.0, 50.0, PLANE + 5.0), 'ring')):
      self.assertEqual(roomOf(point, ways), room, point)
    self.assertLess(roomsInside((0.0, 0.0, PLANE + 70.0), True, ways), 0.0)
    self.assertLess(roomsInside((DECK + 0.5, 0.0, PLANE), True, ways), 0.0)
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    pull = meter.pullAt((DECK, 0.0, PLANE), (0.0, 0.0, 0.0))
    self.assertAlmostEqual(pull[0], G0, 6)
    hub = meter.pullAt((5.0, 0.0, 100.0), (0.0, 0.0, 0.0))
    self.assertLess(math.hypot(*hub), 0.01 * G0)

  def test_hatch(self) -> None:
    """Floating up at 1 m/s under the hatch, docked he goes through it
    into the port and on into the hub; undocked the ceiling stops him."""
    for docked in (True, False):
      world, meter, ways, _ = self._docked(docked)
      cockpit = self._up((0.0, 0.0, NOSE - 1.3), (0.0, 0.0, 1.0),
                         (0.0, 0.0, 1.0))
      self._flown(world, meter, cockpit, 6.0, ways, [])
      z = cockpit.crewman.middle[2]
      if docked:
        self.assertGreater(z, NOSE + 3.0)
        self.assertIn(roomOf(cockpit.crewman.middle, ways), ('port',
                                                             'hub'))
      else:
        self.assertLess(z, NOSE)

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
    """Standing in the cage as it slows to the deck's stop, he stands on
    its floor in the deck when it stops, and its sides along the ring
    are open."""
    world, meter, ways, elevators = self._docked(True)
    car, way = elevators[0], ways[0]
    car.floor = DECK_STOP - 30.0
    car.speed = math.sqrt(2.0 * ACCEL * 30.0)
    car.target = DECK_STOP
    world.stationed(True, ways, self._boxes(elevators, ways))
    middle = tuple((car.floor - 0.95) * w for w in way[:2]) + (PLANE,)
    cockpit = self._up(middle, tuple(car.speed * w for w in way),
                       tuple(-w for w in way))
    self._flown(world, meter, cockpit, 6.0, ways, elevators)
    self.assertTrue(car.atDeck)
    soles = cockpit.crewman.soles()
    self.assertLess(abs(math.hypot(soles[0], soles[1]) - DECK), 0.05)
    boxes = car.boxesOf(way)
    self.assertEqual(boxes[2][0], AWAY)
    self.assertEqual(boxes[3][0], AWAY)
