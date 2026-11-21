"""
TestCabinWorld covers what moves in the cabin, on the device (the CPU
here; user, 2026-11-17: "when can Asger get up and float around in
micro-gravity?"): loose things (the cabin has none since 2026-11-18:
the tests' own on its floor, 'THINGS') rest where they are, on the pad
or weightless; Asger up stands on the floor
under four g, walks in one, pushes off weightless and drifts on, thuds
landing from a jump (as fast as he jumped: it may hurt him). His body
is
a box (user, 2026-11-17: "give Asger the minecraft implementation of
some blocks or whatever rather than just a few balls"; "and make me
able to crouch!"), tried on the pad's open ground: it steps up onto a
step; what is higher, at his knees, trips him; it slides along a wall it walks into at
a slant; crouched it goes under what it cannot stand under, stays
crouched there, and stops at a ledge it would walk off standing; down
steps it keeps to them, no thud.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cabinworld import STILL, CabinWorld, restingLoose
from worQt.gaming.space._cockpit import FLOOR, Cockpit
from worQt.gaming.space._crewman import LOW, MIDDLE, PUSH, STEP
from worQt.gaming.space._crewman import TALL, WIDE
from worQt.gaming.space._launchtower import GROUND

from . import FRAME, SpaceTest

#  The cabin has no loose things (user, 2026-11-18: "remove them
#  completely"); these, on its floor clear of everything, try the loose
#  bodies' physics: each its name, middle, half sizes, axes and mass.
_UPRIGHT = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
THINGS = (('mug', (0.5, 0.0, FLOOR + 0.05), (0.042, 0.042, 0.05),
           _UPRIGHT, 0.35),
          ('kettle', (-0.5, 0.5, FLOOR + 0.115), (0.1, 0.1, 0.115),
           _UPRIGHT, 1.2),
          ('pillow', (0.3, -0.7, FLOOR + 0.06), (0.15, 0.15, 0.06),
           _UPRIGHT, 0.35),
          ('mug', (-0.6, -0.4, FLOOR + 0.05), (0.042, 0.042, 0.05),
           _UPRIGHT, 0.35))

#  Where on the pad's open ground his box is tried (his soles), m.
ARENA = (12.0, 12.0, GROUND)


class TestCabinWorld(SpaceTest):
  """Tests for the cabin's world."""

  #  The kernels compile and step on the CPU here (a frame of 134 bodies
  #  some 0.1 s): minutes, not the default half minute.
  __time_out__ = 900.0

  def _stepped(self, world: CabinWorld, meter: Accelerometer,
               cockpit: Cockpit, seconds: float, want: tuple) -> None:
    """Steps 'world' 'seconds' s a frame at a time, Asger's legs as
    'want' asks (its leap the first frame only)."""
    for k in range(int(round(seconds / FRAME))):
      leap = want[3] if k == 0 else (0.0, 0.0, 0.0)
      world.stepped(FRAME, meter, cockpit.crewman,
                    want[:3] + (leap,))

  def _moved(self, world: CabinWorld) -> float:
    """Returns how far the loose thing that moved most is from where it
    rests, m."""
    return max(math.dist(now[0], rest[0]) for now, rest in zip(
      world.shown(), restingLoose(THINGS)))

  def test_resting(self) -> None:
    """On the pad (one g up) and weightless alike the loose things stay
    where they rest."""
    cockpit = Cockpit()
    for felt in ((0.0, 0.0, G0), (0.0, 0.0, 0.0)):
      world, meter = CabinWorld('cpu', THINGS), self.stillMeter()
      meter.felt = felt
      self._stepped(world, meter, cockpit, 1.0, STILL)
      self.assertLess(self._moved(world), 0.005, felt)

  def test_near(self) -> None:
    """Each loose body's points look only at the solids listed near it
    this frame (user, 2026-11-18: "10 to 30 fps bro...?": each point read
    all four hundred solids each step); none it could meet is left out:
    every solid whose round comes within its reach is listed, and few
    besides."""
    import numpy
    from worQt.gaming.space._cabin_kernels import BODY_NEAR_MOST
    world, meter = CabinWorld('cpu', THINGS), self.stillMeter()
    meter.felt = (0.0, 0.0, G0)
    cockpit = Cockpit()
    self._stepped(world, meter, cockpit, 2.0 * FRAME, STILL)
    counts = world.bodyNearCount.numpy()
    near = world.bodyNear.numpy()
    reaches = world.reaches.numpy()
    places = world.places.numpy()
    middles = world.solidMiddles.numpy()
    halves = numpy.linalg.norm(world.solidHalves.numpy(), axis=1)
    for body in range(1, len(places)):
      self.assertLessEqual(counts[body], BODY_NEAR_MOST, body)
      listed = set(near[body, :counts[body]].tolist())
      apart = numpy.linalg.norm(middles - places[body], axis=1)
      meets = set(numpy.nonzero(apart < reaches[body] + halves)[0].tolist())
      self.assertLessEqual(meets, listed, body)
      self.assertLess(len(listed), len(middles) // 4, body)

  def test_standing(self) -> None:
    """Up under four g he stands on the floor; in one g he walks back
    from his chair at most at his stride (a third of a second: then the
    hull leaning in over him meets his box's top)."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, 4.0 * G0)
    cockpit.gotUp()
    self._stepped(world, meter, cockpit, 1.0, STILL)
    crewman = cockpit.crewman
    self.assertLess(abs(crewman.soles()[2] - FLOOR), 0.02)
    self.assertTrue(crewman.touches)
    meter.felt = (0.0, 0.0, G0)
    began = crewman.middle
    for _ in range(20):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      want = crewman.wantOf({'back'}, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))
    gone = began[0] - crewman.middle[0]
    self.assertGreater(gone, 0.7)
    self.assertLess(gone, 1.0)

  def test_floating(self) -> None:
    """Weightless he pushes off the floor and drifts on up, slowing
    only a little in the air."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, 0.0)
    cockpit.gotUp()
    crewman = cockpit.crewman
    self._stepped(world, meter, cockpit, 0.1, STILL)
    self.assertTrue(crewman.touches)
    leap = crewman.leapOf((0.0, 0.0, 0.0))
    self.assertClose(leap, (0.0, 0.0, PUSH), 1e-6)
    low = crewman.middle[2]
    self._stepped(world, meter, cockpit, 0.3, STILL[:3] + (leap,))
    self.assertGreater(crewman.middle[2] - low, 0.55)
    self.assertGreater(crewman.velocity[2], 0.95 * PUSH)
    self.assertFalse(crewman.touches)

  def test_thud(self) -> None:
    """Landing from a jump in one g thuds, and lands about as fast as
    he jumped."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    self._stepped(world, meter, cockpit, 0.2, STILL)
    crewman = cockpit.crewman
    leap = crewman.leapOf((0.0, 0.0, -G0))
    before, landed = world.thuds, 0.0
    for k in range(60):
      world.stepped(FRAME, meter, crewman, STILL[:3] + (
        leap if k == 0 else (0.0, 0.0, 0.0),))
      landed = max(landed, world.landed)
    self.assertGreater(world.thuds, before)
    self.assertLess(abs(landed - leap[2]), 0.5)

  def _arena(self, boxes: tuple) -> tuple:
    """Returns his cockpit (him up on the open ground at 'ARENA', facing
    x), the world with 'boxes' there (each its low and high corners from
    'ARENA') and the pad's pull (one g)."""
    cockpit, meter = Cockpit(), self.stillMeter()
    world = CabinWorld('cpu')
    meter.felt = (0.0, 0.0, G0)
    cockpit.gotUp()
    world.walked(1)
    solids = []
    for low, high in boxes:
      low = tuple(a + b for a, b in zip(ARENA, low))
      high = tuple(a + b for a, b in zip(ARENA, high))
      solids.append((tuple(0.5 * (a + b) for a, b in zip(low, high)),
                     tuple(0.5 * (b - a) for a, b in zip(low, high)),
                     (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0)))
    world.stationed(False, (), tuple(solids))
    crewman = cockpit.crewman
    crewman.placed((ARENA[0], ARENA[1], ARENA[2] + 0.002 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    crewman.up, crewman.ahead = (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)
    cockpit.yaw, cockpit.pitch = 0.0, 0.0
    return cockpit, world, meter

  def _walked(self, world: CabinWorld, meter: Accelerometer,
              cockpit: Cockpit, held: set, seconds: float,
              crouch: bool = False) -> None:
    """Walks him 'seconds' s a frame at a time, the keys 'held' (crouched
    if 'crouch')."""
    crewman = cockpit.crewman
    crewman.crouching = crouch
    for _ in range(max(1, int(round(seconds / FRAME)))):
      pull = meter.pullAt(crewman.middle, crewman.velocity)
      cockpit.yaw, cockpit.pitch, _ = crewman.righted(
        pull, FRAME, cockpit.yaw, cockpit.pitch)
      want = crewman.wantOf(held, cockpit.yaw, cockpit.pitch, pull)
      world.stepped(FRAME, meter, crewman, want + ((0.0, 0.0, 0.0),))

  def _soles(self, cockpit: Cockpit) -> tuple:
    """Returns his soles from 'ARENA'."""
    return tuple(s - a for s, a in zip(cockpit.crewman.soles(), ARENA))

  def test_step(self) -> None:
    """Walking ahead he steps up onto a block lower than 'STEP' and
    walks on across it; a block higher than that, at his knees, trips
    him (user, 2026-11-18: "if you hit Asgers legs like that he should
    start spinning"): a thud, he falls onto it; let go, he stands up
    again before it, flush."""
    low = 0.8 * STEP
    cockpit, world, meter = self._arena((((0.6, -1.0, -0.2), (2.6, 1.0,
                                                               low)),))
    self._walked(world, meter, cockpit, set(), 0.2)
    self._walked(world, meter, cockpit, {'ahead'}, 1.0)
    soles = self._soles(cockpit)
    self.assertGreater(soles[0], 1.2)
    self.assertLess(abs(soles[2] - low), 0.01)
    self.assertTrue(cockpit.crewman.touches)
    high = 1.5 * STEP
    cockpit, world, meter = self._arena((((0.6, -1.0, -0.2), (2.6, 1.0,
                                                               high)),))
    self._walked(world, meter, cockpit, set(), 0.2)
    fell = False
    for _ in range(int(round(1.0 / FRAME))):
      self._walked(world, meter, cockpit, {'ahead'}, FRAME)
      fell = fell or cockpit.crewman.fallen
    self.assertTrue(fell)
    self.assertGreater(world.thuds, 0)
    self._walked(world, meter, cockpit, set(), 2.0)
    soles = self._soles(cockpit)
    self.assertFalse(cockpit.crewman.fallen)
    self.assertLess(abs(soles[2]), 0.01)
    self.assertLess(abs(soles[0] + 0.5 * WIDE - 0.6), 0.01)

  def test_slide(self) -> None:
    """Walking into a wall at a slant he slides along it, his middle
    flush with it (leaning on it a little), not stopped."""
    cockpit, world, meter = self._arena((((0.6, -3.0, -0.2), (1.0, 3.0,
                                                               2.0)),))
    cockpit.crewman.ahead = (math.cos(0.5), math.sin(0.5), 0.0)
    self._walked(world, meter, cockpit, set(), 0.2)
    self._walked(world, meter, cockpit, {'ahead'}, 1.0)
    middle = cockpit.crewman.middle
    self.assertLess(abs(middle[0] - ARENA[0] + 0.5 * WIDE - 0.6), 0.02)
    self.assertGreater(middle[1] - ARENA[1], 1.0)

  def test_crouch(self) -> None:
    """Under a slab between his crouched and his standing height,
    crouched he walks under it, slower, and stays crouched there let
    go; out from under it he stands again (standing, he bumps his head
    on it: 'test_knocks')."""
    over = 0.5 * (LOW + TALL)
    slab = ((0.6, -1.0, over), (2.0, 1.0, over + 0.1))
    cockpit, world, meter = self._arena((slab,))
    self._walked(world, meter, cockpit, set(), 0.2)
    self._walked(world, meter, cockpit, {'ahead'}, 1.2, True)
    crewman = cockpit.crewman
    self.assertTrue(crewman.crouched)
    self.assertGreater(self._soles(cockpit)[0], 0.8)
    self._walked(world, meter, cockpit, set(), 0.3, False)
    self.assertTrue(crewman.crouched)
    self._walked(world, meter, cockpit, {'ahead'}, 2.0, True)
    self._walked(world, meter, cockpit, {'ahead'}, 0.6, False)
    self.assertGreater(self._soles(cockpit)[0], 2.3)
    self.assertFalse(crewman.crouched)

  def test_ledge(self) -> None:
    """On a platform crouched he stops at its edge; standing he walks
    off it and falls."""
    deck = ((-2.0, -1.0, -0.2), (1.0, 1.0, 0.5))
    for crouch in (True, False):
      cockpit, world, meter = self._arena((deck,))
      crewman = cockpit.crewman
      crewman.placed((ARENA[0], ARENA[1], ARENA[2] + 0.502 + MIDDLE),
                     (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
      self._walked(world, meter, cockpit, set(), 0.2, crouch)
      self._walked(world, meter, cockpit, {'ahead'}, 2.0, crouch)
      soles = self._soles(cockpit)
      if crouch:
        self.assertLess(abs(soles[2] - 0.5), 0.01)
        self.assertLess(soles[0], 1.0 + 0.5 * WIDE)
      else:
        self.assertLess(abs(soles[2]), 0.01)
        self.assertGreater(soles[0], 1.0 + 0.5 * WIDE)

  def test_down(self) -> None:
    """Walking down steps he keeps to them: no thud, never off them more
    than a hair."""
    rise, run = 0.2, 0.3
    steps = tuple(((run * k, -1.0, -0.2), (run * (k + 1), 1.0,
                                           rise * (4 - k)))
                  for k in range(4))
    cockpit, world, meter = self._arena(((((-2.0, -1.0, -0.2), (0.0, 1.0,
                                                                 0.8)),)
                                         + steps))
    crewman = cockpit.crewman
    crewman.placed((ARENA[0] - 1.0, ARENA[1], ARENA[2] + 0.802 + MIDDLE),
                   (0.0, 0.0, 0.0), 0, (0.0, 0.0, 0.0))
    self._walked(world, meter, cockpit, set(), 0.2)
    before = world.thuds
    for _ in range(int(round(1.6 / FRAME))):
      self._walked(world, meter, cockpit, {'ahead'}, FRAME)
      self.assertTrue(crewman.touches, crewman.middle)
    self.assertEqual(world.thuds, before)
    self.assertGreater(self._soles(cockpit)[0], 1.3)
    self.assertLess(abs(self._soles(cockpit)[2]), 0.01)
