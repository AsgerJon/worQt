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
from worQt.gaming.space._elevator import HUB_STOP, Elevator, backBoxes
from worQt.gaming.space._station import SPIN
from worQt.gaming.space._stationinterior import DECK, PLANE, roomOf
from worQt.gaming.space._stationinterior import roomsInside, shaftWays

from . import FRAME, SpaceTest

#  The docked rocket's own axes in the station's: its nose down the
#  station's axis, unrolled.
RELATIVE = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
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
    world.stationed(docked, ways, self._boxes(elevators, ways))
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    return world, meter, ways, elevators

  def _boxes(self, elevators: list, ways: tuple) -> tuple:
    """Returns every elevator's plates and the cages' back walls (the
    station turning as the accelerometer has it)."""
    return tuple(box for elevator, way in zip(elevators, ways)
                 for box in elevator.boxesOf(way)) + backBoxes(
      ways, (0.0, 0.0, -SPIN))

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
    into the port, the hub (the other port past it, shut), the shafts
    and the ring; on the deck the
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
    self.assertEqual(roomOf((0.0, 0.0, PLANE + 70.0), ways), 'far port')
    self.assertLess(roomsInside((0.0, 0.0, PLANE + 85.0), True, ways), 0.0)
    self.assertLess(roomsInside((DECK + 0.5, 0.0, PLANE), True, ways), 0.0)
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    pull = meter.pullAt((DECK, 0.0, PLANE), (0.0, 0.0, 0.0))
    self.assertAlmostEqual(pull[0], G0, 6)
    hub = meter.pullAt((5.0, 0.0, 100.0), (0.0, 0.0, 0.0))
    self.assertLess(math.hypot(*hub), 0.01 * G0)

  def test_way_up(self) -> None:
    """Docked, the way up the axis from the cabin's floor through the
    hatch and the port into the hub is a room all along, never shallower
    than his box's half width near the axis (rooms meeting at a plane are
    nought deep there: his box stopped dead under the hub's mouth, the
    user's let's play, 2026-11-18)."""
    from worQt.gaming.space._crewman import WIDE
    from worQt.gaming.space._stationinterior import HUB_LOW
    ways = shaftWays(RELATIVE)
    z = 24.5
    while z < HUB_LOW + 10.0:
      for x, y in ((0.0, 0.0), (0.25, 0.0), (0.0, -0.25)):
        self.assertGreater(roomsInside((x, y, z), True, ways), 0.5 * WIDE,
                           (x, y, z))
      z += 0.05

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

  def _pulled(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, bolt: tuple, seconds: float) -> tuple:
    """Pulls Asger by the Grav-Gun to 'bolt' for 'seconds' s, his eyes
    on it; returns the gun and the hardest meeting."""
    from worQt.gaming.space._crewman import HEFT
    from worQt.gaming.space._gravgun import GravGun
    gun, crewman, hardest = GravGun(), cockpit.crewman, 0.0
    gun.gripped(('bolt', 0))
    for _ in range(int(round(seconds / FRAME))):
      crewman.righted(meter.pullAt(crewman.middle, crewman.velocity),
                      FRAME)
      eye = cockpit.eye()
      look = tuple(b - e for b, e in zip(bolt[0], eye))
      size = math.sqrt(sum(x * x for x in look))
      look = tuple(x / size for x in look)
      muzzle = tuple(e + 0.75 * x for e, x in zip(eye, look))
      force = gun.pushOf(muzzle, look, crewman.middle, bolt[0], tuple(
        -v for v in crewman.velocity), HEFT, FRAME)
      world.stepped(FRAME, meter, crewman, STILL, (
        tuple(f / HEFT for f in force), None, (0.0, 0.0, 0.0)))
      hardest = max(hardest, world.landed)
    return gun, hardest

  def test_out_along(self) -> None:
    """From the hub's middle bolt the Grav-Gun pulls him out to a
    spoke's mouth (user, 2026-11-18: "when Asger moves out of the spoke,
    the wall of it should push Asger"; "can we just extend the four
    'back' walls towards the center, so Asger can begin to move along
    side them sooner until he gets to the elevator"): the station's turn
    brings the cage's back wall against him early and it pushes him
    round, unhurt (no wall in the way, he met the hub's wall beside the
    mouth at 13 m/s); held at the mouth's bolt, then pulled into the
    cage; the next spoke's wall nowhere in his way."""
    from worQt.gaming.space._bolts import holdOf, stationBolts
    from worQt.gaming.space._vitals import HEALTH, Vitals
    world, meter, ways, elevators = self._docked(True)
    bolts = stationBolts(ways, tuple(e.floor for e in elevators))
    for k in (0, 1):
      cockpit = self._up(holdOf(bolts[6]), (0.0, 0.0, 0.0),
                         (0.0, 0.0, 1.0))
      world.teleported()
      world.stationed(True, ways, self._boxes(elevators, ways))
      gun, hardest = self._pulled(world, meter, cockpit, bolts[7 + k],
                                  9.0)
      self.assertTrue(gun.holding, k)
      crewman = cockpit.crewman
      self.assertLess(math.dist(crewman.middle, bolts[7 + k][0]), 1.0)
      vitals = Vitals()
      vitals.fell(hardest)
      self.assertEqual(vitals.health, HEALTH, (k, hardest))
      gun, hardest = self._pulled(world, meter, cockpit, bolts[11 + k],
                                  4.0)
      self.assertTrue(elevators[k].holds(ways[k], crewman.middle), k)
      vitals.fell(hardest)
      self.assertEqual(vitals.health, HEALTH, (k, hardest))

  def test_far_door(self) -> None:
    """Docked, the far port (the one the rocket is not in) is shut by a
    door over its docking ring's hatch (user, 2026-11-18: "Fix the far
    port stuff": its hole showed space): wider than the hole, at the
    far end of that port's room, facing in, shown only docked."""
    from worQt.gaming.space._dashboard import pieceRows
    from worQt.gaming.space._stationinterior import FAR_HIGH, FAR_LOW
    from worQt.gaming.space._stationinterior import HATCH, PORT_INSIDE
    from worQt.gaming.space._stationinterior import tubeInside
    rows, _ = pieceRows(('port door', 0), {})
    across = max(math.hypot(r[0], r[1]) for r in rows)
    self.assertGreater(across, HATCH + 0.1)
    self.assertLess(across, PORT_INSIDE)
    place = (0.0, 0.0, FAR_HIGH - 0.05)
    deep = tubeInside(place, PORT_INSIDE, FAR_LOW, FAR_HIGH)
    self.assertAlmostEqual(deep, 0.05, 9)
    self.assertLess(max(r[2] for r in rows), 1e-9)

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
