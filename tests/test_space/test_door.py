"""
TestDoor covers the rocket's main door (user, 2026-11-18: "And a real
door."; '_door'): its motor opens it all the way and its latch holds it;
it shuts; it locks only shut and locked it will not open; its leaf is a
solid in the doorway shut and clear of it open; closing on Asger
standing in the doorway, it stops against him and opens again, never
through him; floating there weightless, he is pushed aside by it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabin_kernels import BOX_HALF
from worQt.gaming.space._cabinworld import STILL, CabinWorld
from worQt.gaming.space._cockpit import FLOOR, Cockpit
from worQt.gaming.space._crewman import MIDDLE
from worQt.gaming.space._door import MIDDLE_FAR, TRAVEL, Door
from worQt.gaming.space._turns import dot
from worQt.gaming.space._walkway import DOORWAY

from . import FRAME, SpaceTest

#  Where he stands in the doorway (his soles), m: in the leaf's way.
STANDS = (-4.75, 0.1, FLOOR + 0.002)


class TestDoor(SpaceTest):
  """Tests for the main door."""

  #  The cabin's kernels step on the CPU here: minutes.
  __time_out__ = 900.0

  def test_motor(self) -> None:
    """Sent open it goes all the way within two seconds and is held
    there; sent shut it shuts; it locks only shut; locked it will not
    open."""
    door = Door(False)
    self.assertTrue(door.shut)
    self.assertEqual(door.opened(), '')
    for _ in range(int(2.0 / FRAME)):
      door.moved(FRAME, 0.0, 0.0)
    self.assertEqual(door.arc, TRAVEL)
    self.assertIsNone(door.target)
    self.assertTrue(door.passable)
    self.assertEqual(door.locking(), 'close the door first')
    self.assertEqual(door.closed(), '')
    for _ in range(int(2.0 / FRAME)):
      door.moved(FRAME, 0.0, 0.0)
    self.assertTrue(door.shut)
    self.assertEqual(door.locking(), '')
    self.assertEqual(door.opened(), 'the door is locked')

  def test_leaf(self) -> None:
    """Shut, its leaf fills the doorway (across it, the whole of its
    width and height); open, it is clear of it."""
    door = Door(False)
    middle, half, _, _ = door.boxOf()
    (x0, y0, z0), (x1, y1, z1) = DOORWAY
    self.assertGreater(middle[0], x0)
    self.assertLess(middle[0], x1)
    self.assertGreater(half[1], 0.5 * (y1 - y0))
    self.assertGreater(2.0 * half[2], z1 - z0)
    door.arc = TRAVEL
    middle, half, _, _ = door.boxOf()
    self.assertLess(middle[1] + half[1], y0)

  def _world(self, felt: tuple) -> tuple:
    """Returns his cockpit (him standing in the doorway, facing out),
    the world with the doorway and the walkway joined and the door open
    in it, the door, and a meter feeling 'felt'."""
    cockpit, meter = Cockpit(), self.stillMeter()
    meter.felt = felt
    world = CabinWorld('cpu')
    world.walked(3)
    cockpit.gotUp()
    crewman = cockpit.crewman
    crewman.placed((STANDS[0], STANDS[1], STANDS[2] + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0)
    cockpit.yaw, cockpit.pitch = 0.0, 0.0
    door = Door(False)
    door.arc = TRAVEL
    world.doorPlaced(*door.boxOf())
    return cockpit, world, door, meter

  def _stepped(self, cockpit: Cockpit, world: CabinWorld, door: Door,
               meter: object, seconds: float) -> float:
    """Steps them 'seconds' s, as the window does ('_doorMoved'): the
    door pushed by what he pushed its leaf by, its leaf put anew; returns
    how near the leaf's edge came to him across its way, m (below nought:
    into his box)."""
    crewman = cockpit.crewman
    nearest = 1e9
    for _ in range(int(round(seconds / FRAME))):
      push = world.struck(-1, 1)[1][2] / MIDDLE_FAR
      door.moved(FRAME, 0.0, push)
      world.doorPlaced(*door.boxOf())
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      crewman.righted(pull, FRAME, cockpit.yaw, cockpit.pitch)
      want = crewman.wantOf(set(), cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))
      way, middle = door.wayAt()
      edge = dot(middle, way) - door.boxOf()[1][1]
      reach = BOX_HALF * (abs(way[0]) + abs(way[1]))
      nearest = min(nearest, edge - dot(crewman.middle, way) - reach)
    return nearest

  def test_stopped(self) -> None:
    """Closing on him standing in the doorway (one g), its leaf stops
    against him, never into him, and it opens again; he stays."""
    cockpit, world, door, meter = self._world((0.0, 0.0, G0))
    self._stepped(cockpit, world, door, meter, 0.3)
    before = cockpit.crewman.middle
    self.assertEqual(door.closed(), '')
    nearest = self._stepped(cockpit, world, door, meter, 3.0)
    self.assertGreater(nearest, -0.02)
    self.assertTrue(door.wanted)
    self.assertLess(abs(cockpit.crewman.middle[1] - before[1]), 0.1)

  def test_pushed(self) -> None:
    """Floating weightless in the doorway, its leaf closing pushes him
    on along its way (till the doorway's side stops him), and it opens
    again."""
    cockpit, world, door, meter = self._world((0.0, 0.0, 0.0))
    self._stepped(cockpit, world, door, meter, 0.1)
    before = cockpit.crewman.middle
    self.assertEqual(door.closed(), '')
    nearest = self._stepped(cockpit, world, door, meter, 3.0)
    self.assertGreater(nearest, -0.02)
    way, _ = door.wayAt()
    moved = tuple(a - b for a, b in zip(cockpit.crewman.middle, before))
    self.assertLess(dot(moved, way), -0.05)
    self.assertTrue(door.wanted)
