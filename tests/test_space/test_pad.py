"""
TestPad covers the launch pad as its own place on Terra (user,
2026-11-18: "bro, the pad needs to be there. If Asger took a shit on the
ground before launch, upon return there'd still be a turd on the
ground"; '_pad'): its ground feels Terra's pull less its turning's, and
turns as Terra does; a rocket stood on it is where the pad's axes have
it, still, and stays so as Terra carries both round; the ways between
the rocket's axes and the pad's undo each other; in the pad's world
Asger stands in the tower's hall whatever the rocket does (lifted off,
he stays); walking the walkway he stops at the rocket's shut door, and
with the rocket gone he walks on to the walkway's end; standing in it
as it folds (user, 2026-11-18: "harmonica away"), its floor carries
him; with it gone, he walks out of the hall into the air and falls;
its seal presses the hull as it is fitted to and stops its motor; what
he pushes the rocket's legs and body by is the rocket's, the tower's
the pad's.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._crewman import HEFT, MIDDLE
from worQt.gaming.space._door import Door
from worQt.gaming.space._launchtower import START, towerSolids
from worQt.gaming.space._pad import Pad, fromPad, movingFromPad
from worQt.gaming.space._pad import movingToPad, posesOf, toPad
from worQt.gaming.space._planets import PAD
from worQt.gaming.space._turns import aboutAxis, norm, rotated, unit
from worQt.gaming.space._vessel import Vessel
from worQt.gaming.space._walkway import HELD, OUT_MOST, SEAL_FIT
from worQt.gaming.space._walkway import SECTION_LONG, SECTIONS, Walkway
from worQt.gaming.space._cockpit import FLOOR, capsuleRadius
from worQt.gaming.space._cabinworld import PAD_FACES, ROCKET_FACES
from worQt.gaming.space._launchtower import GROUND, rocketLegs

from . import FRAME, SpaceTest

_AXES = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
#  The rocket's pose in the pad's axes where it stands, and gone.
STILL = ((0.0, 0.0, 0.0), _AXES, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))
GONE = ((0.0, 0.0, 1e5), _AXES, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0))


class TestPad(SpaceTest):
  """Tests for the pad's place on Terra."""

  #  The cabin's kernels step on the CPU here: minutes.
  __time_out__ = 900.0

  def test_felt(self) -> None:
    """Its ground feels about one g up (Terra's pull less what carrying
    it round takes), nothing much across; it turns as Terra turns: up
    by the sine of its latitude, north by its cosine, not east."""
    system = self.systemOf()
    pad = Pad(system)
    felt, turning = pad.feltOf(system, 0.0)
    self.assertGreater(felt[2], 9.76)
    self.assertLess(felt[2], 9.84)
    self.assertLess(math.hypot(felt[0], felt[1]), 0.05)
    spin = system.bodies[pad.anchor].spin
    lat = math.radians(PAD[0])
    self.assertLess(abs(turning[0]), 1e-12)
    self.assertLess(abs(turning[1] - spin * math.cos(lat)), 1e-9)
    self.assertLess(abs(turning[2] - spin * math.sin(lat)), 1e-9)

  def test_rocket(self) -> None:
    """A rocket stood on the pad is where its axes have it, still, and
    is so a minute on, carried round with Terra."""
    system = self.systemOf()
    pad, vessel = Pad(system), Vessel()
    vessel.stood(system, pad.anchor, PAD[0], PAD[1], 0.0)
    for t in (0.0, 60.0):
      if t:
        vessel.carried(system, t)
      place, axes, moving, spin = pad.rocketIn(vessel, system, t)
      self.assertLess(norm(place), 1e-3)
      for got, want in zip(axes, _AXES):
        self.assertLess(norm(tuple(a - b for a, b in zip(got, want))),
                        1e-9)
      self.assertLess(norm(moving), 1e-6)
      self.assertLess(norm(spin), 1e-9)

  def test_ways(self) -> None:
    """Into the pad's axes and back is no way at all, the rocket leant,
    off and moving; its poses put each where the other has it."""
    turn = aboutAxis(unit((0.3, -0.4, 0.866)), 0.2)
    rocket = ((1.0, -2.0, 0.5), tuple(rotated(turn, e) for e in _AXES),
              (0.1, 0.2, -0.3), (0.01, -0.02, 0.03))
    point, moving = (0.4, 0.7, 1.9), (1.5, -0.5, 0.25)
    back = fromPad(rocket, toPad(rocket, point))
    self.assertLess(norm(tuple(a - b for a, b in zip(back, point))), 1e-12)
    there = toPad(rocket, point)
    again = movingFromPad(rocket, there, movingToPad(rocket, point,
                                                      moving))
    self.assertLess(norm(tuple(a - b for a, b in zip(again, moving))),
                    1e-12)
    cabin, inPad = posesOf(rocket)
    padPlace = cabin[1][0]
    self.assertLess(norm(toPad(rocket, padPlace)), 1e-12)
    self.assertEqual(inPad[0][0], rocket[0])

  def _padWorld(self, rocket: tuple) -> tuple:
    """Returns his cockpit (him standing at the tower's start, facing
    the rocket), the pad's world (the tower's rooms and solids, the
    rocket where 'rocket' has it, its door shut) and the pad's meter."""
    system = self.systemOf()
    meter = Accelerometer()
    meter.grounded(*Pad(system).feltOf(system, 0.0))
    world = CabinWorld('cpu', (), False)
    world.walked(3)
    world.stationed(False, (), towerSolids())
    legs = tuple((toPad(rocket, m), h, t, v) for m, h, t, v in
                 rocketLegs())
    world.restationed(len(towerSolids()), Walkway(True).boxesOf() + legs)
    self._posed(world, rocket)
    cockpit = Cockpit()
    cockpit.gotUp()
    crewman = cockpit.crewman
    soles = START[0]
    crewman.placed((soles[0], soles[1], soles[2] + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    cockpit.yaw, cockpit.pitch = 0.0, 0.0
    return cockpit, world, meter

  def _posed(self, world: CabinWorld, rocket: tuple) -> None:
    """Puts the rocket in the pad's world where 'rocket' has it, its
    door shut."""
    world.posed(*posesOf(rocket)[1])
    middle, half, turn, moving = Door(True).boxOf()
    world.doorPlaced(toPad(rocket, middle), half, turn, moving)

  def _walked(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, held: set, seconds: float) -> None:
    """Walks him 'seconds' s a frame at a time, the keys 'held'."""
    crewman = cockpit.crewman
    for _ in range(max(1, int(round(seconds / FRAME)))):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      cockpit.yaw, cockpit.pitch, _ = crewman.righted(
        pull, FRAME, cockpit.yaw, cockpit.pitch)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))

  def test_stays(self) -> None:
    """Standing in the tower's hall, he feels one g and stands; the
    rocket lifted off, he stands on where he stood."""
    cockpit, world, meter = self._padWorld(STILL)
    self._walked(world, meter, cockpit, set(), 0.5)
    crewman = cockpit.crewman
    before = crewman.middle
    self.assertTrue(crewman.touches)
    self._posed(world, GONE)
    self._walked(world, meter, cockpit, set(), 1.0)
    self.assertLess(math.dist(crewman.middle, before), 0.01)
    self.assertTrue(crewman.touches)
    self.assertGreater(crewman.up[2], 0.999)
    self.assertLess(abs(meter.pullAt(crewman.middle, crewman.velocity)[2]
                        + G0), 0.05)

  def test_folded(self) -> None:
    """Standing in the walkway as it folds, its floor carries him in
    toward the tower; while it folds he never falls through it (he
    rides each smaller section's edge as it comes to him, so folded he
    stands at its far end: off it, he falls)."""
    cockpit, world, meter = self._padWorld(STILL)
    walkway = Walkway(True)
    first = len(towerSolids())
    world.restationed(first, walkway.boxesOf())
    crewman = cockpit.crewman
    crewman.placed((-9.0, 0.0, FLOOR + 0.2 + MIDDLE), (0.0, 0.0, 0.0), 0,
                   (0.0, 0.0, 0.0))
    world.teleported()
    world.walked(3)
    world.stationed(False, (), towerSolids())
    self._posed(world, STILL)
    world.restationed(first, walkway.boxesOf())
    self._walked(world, meter, cockpit, set(), 0.5)
    before = crewman.middle
    walkway.dismissed()
    lowest = before[2]
    for _ in range(int(8.0 / FRAME)):
      along, about = walkway.loadsOf(tuple(
        world.struck(first + 4 * k, 4) for k in range(SECTIONS)))
      walkway.moved(FRAME, along, about)
      world.restationed(first, walkway.boxesOf())
      self._walked(world, meter, cockpit, set(), FRAME)
      if walkway.long > SECTION_LONG + 0.05:
        lowest = min(lowest, crewman.middle[2])
    self.assertLess(crewman.middle[0], before[0] - 1.5)
    self.assertGreater(lowest, before[2] - 0.2)

  def test_fell(self) -> None:
    """With no walkway, out of the hall's hole he falls to the ground
    (swung away, it stands across the hole: it pivots there)."""
    cockpit, world, meter = self._padWorld(STILL)
    world.stationed(False, (), towerSolids())
    crewman = cockpit.crewman
    self._walked(world, meter, cockpit, set(), 0.3)
    top = crewman.middle[2]
    self._walked(world, meter, cockpit, {'ahead'}, 6.0)
    self.assertLess(crewman.middle[2], top - 20.0)

  def test_seal(self) -> None:
    """Out at the door the walkway's seal presses the rocket's hull as
    hard as it is fitted to, into it; the rocket off a little, it
    presses nothing; driven out, its motor stops once its seal presses
    so hard, short of its furthest (user, 2026-11-18: "Use a soft
    inflatable thing like for airliners")."""
    walkway = Walkway(True)
    pressed, point = walkway.sealOf(STILL)
    self.assertLess(abs(norm(pressed) - SEAL_FIT), 0.05 * SEAL_FIT)
    self.assertGreater(pressed[0], 0.0)
    self.assertLess(abs(point[0] + capsuleRadius(FLOOR)), 0.15)
    off = ((0.3, 0.0, 0.0),) + STILL[1:]
    self.assertEqual(walkway.sealOf(off)[0], (0.0, 0.0, 0.0))
    walkway.long, walkway.outTarget = HELD - 1.0, OUT_MOST
    for _ in range(int(10.0 / FRAME)):
      walkway.moved(FRAME, 0.0, 0.0, STILL)
      if walkway.outTarget is None:
        break
    self.assertIsNone(walkway.outTarget)
    self.assertLess(walkway.long, OUT_MOST - 0.01)
    self.assertGreater(norm(walkway.sealOf(STILL)[0]), 0.5 * SEAL_FIT)

  def _shoved(self, soles: tuple, ahead: tuple, first: int,
              count: int) -> tuple:
    """Returns what he pushed solids 'first' on ('count' of them; or the
    rooms' faces: 'CabinWorld.struck') by, summed over two seconds
    walking from 'soles' (the pad's axes) the way 'ahead'."""
    cockpit, world, meter = self._padWorld(STILL)
    crewman = cockpit.crewman
    crewman.placed((soles[0], soles[1], soles[2] + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.ahead = ahead
    self._walked(world, meter, cockpit, set(), 0.3)
    total = [0.0, 0.0, 0.0]
    for _ in range(int(2.0 / FRAME)):
      self._walked(world, meter, cockpit, {'ahead'}, FRAME)
      total = [a + b for a, b in zip(total, world.struck(first, count)[0])]
    return tuple(total)

  def test_shoved(self) -> None:
    """Walking into a rocket's foot (and onto it: he trips up onto it),
    he pushes its legs (the rocket's: user, 2026-11-18, "rocket legs are
    part of the rocket. If Asger pushes hard enough to rocket should fall
    over"); into its body from the yard, its face (the rocket's); into
    the stair tower's wall, nothing of the rocket's: the tower's and the
    ground's faces (Terra's) carry it, and his weight."""
    first = len(towerSolids()) + len(Walkway(True).boxesOf())
    legs = self._shoved((0.0, 12.0, GROUND + 0.002), (0.0, -1.0, 0.0),
                        first, len(rocketLegs()))
    self.assertGreater(norm(legs), 20.0)
    side = math.sqrt(0.5)
    body = self._shoved((7.5 * side, 7.5 * side, GROUND + 0.002),
                        (-side, -side, 0.0), ROCKET_FACES, 1)
    self.assertLess(body[0] + body[1], -20.0)
    tower = self._shoved((-15.5, 0.0, GROUND + 0.002), (-1.0, 0.0, 0.0),
                         ROCKET_FACES, 1)
    self.assertLess(norm(tower), 1.0)
    ground = self._shoved((-15.5, 0.0, GROUND + 0.002), (-1.0, 0.0, 0.0),
                          PAD_FACES, 1)
    self.assertLess(ground[2], -0.9 * HEFT * G0 * 2.0)

  def test_walkway(self) -> None:
    """Walking the walkway he stops at the rocket's shut door (leaning
    on its leaf: it leans with the hull, his shins meet it first); with
    the rocket gone he walks on to the walkway's end, past where its
    hull was."""
    cockpit, world, meter = self._padWorld(STILL)
    self._walked(world, meter, cockpit, set(), 0.3)
    self._walked(world, meter, cockpit, {'ahead'}, 6.0)
    self.assertLess(cockpit.crewman.middle[0], -4.6)
    self.assertGreater(cockpit.crewman.middle[0], -5.5)
    cockpit, world, meter = self._padWorld(GONE)
    self._walked(world, meter, cockpit, set(), 0.3)
    self._walked(world, meter, cockpit, {'ahead'}, 6.0)
    self.assertGreater(cockpit.crewman.middle[0], -4.0)
