"""
TestContact covers 'Contact', two bodies let touch, their edges lines
of little springs: a box dropped onto a slab on the ground comes to
rest on it, sunk its weight over the stiffness times the length of its
bottom edges, held along them, the books balancing; a run cut on its
steps goes on as whole, the holds kept; on the hexapod, a box rests on
the platform, the legs carrying both; tilted gentler than its grip it
stays put on the platform, steeper it slides off; heaved gently it
rides along, never letting go, heaved past gravity it hops; two welded
boxes do not touch each other.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Books, Contact
from worQt.phys import Ground, HeldPose, Hexapod, State, SwayingPose
from worQt.phys import Weld, World, boxShape, conjugate, minus, norm
from worQt.phys import rotated

from . import PhysTest

GROUND = World((0.0, 0.0, -9.81), 1e-3, Ground())
BOUND = World((0.0, 0.0, -9.81), 2.5e-4, Ground())
WORLD = World()
SLAB = Body.of(boxShape(0.6, 0.6, 0.2), 1000.0)
BOX = Body.of(boxShape(0.3, 0.3, 0.2), 1000.0)
STACK = Assembly((SLAB, BOX), (Contact(0, 1),))
PLATE = Body.of(boxShape(1.4, 1.4, 0.05), 2700.0)
RIG = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, -0.025)
HELD = HeldPose((0.0, 0.0, 1.0))
BOTTOM = tuple(share for point, share in BOX.shape.skin(0.01)
               if abs(point[2] + 0.1) < 1e-12)


def onPlatform(motion: object) -> tuple[Assembly, tuple]:
  """The 'onPlatform' function returns the box on the hexapod moving as
  'motion' says, and the two as they start: the box just above the
  platform's middle."""
  rig = Assembly((PLATE, BOX), RIG.legs(PLATE, 0, motion) + (
    Contact(0, 1),))
  return rig, (motion.at(0.0).state(), State((0.0, 0.0, 1.126)))


class TestContact(PhysTest):
  """Tests for 'Contact'."""

  def test_stacked(self) -> None:
    """A box dropped onto a slab on the ground comes to rest on it, the
    slab sunk the weights over its four corners' stiffness on the
    ground, the box its weight over the stiffness times the length its
    bottom edges' points hold, held at every one of them, the books
    balancing."""
    states = (State((0.0, 0.0, 0.1)), State((0.05, 0.02, 0.35)))
    held = GROUND.storedOf(STACK, states).total()
    states, books = GROUND.booked(STACK, states, 2.0, 0.0, Books())
    both = (SLAB.mass + BOX.mass) * 9.81 / (4.0 * 1e5)
    sunk = BOX.mass * 9.81 / (1e6 * sum(BOTTOM))
    self.assertAlmostEqual(states[0].place[2], 0.1 - both, 4)
    self.assertAlmostEqual(states[1].place[2], 0.3 - both - sunk, 4)
    self.assertLess(norm(states[1].velocity), 1e-3)
    self.assertEqual(len(states[1].holds), len(BOTTOM))
    self.assertEqual({other for _, other, *_ in states[1].holds}, {0})
    self.assertEqual(len(states[0].bristles), 4)
    self.assertGreater(books.contacts, 1.0)
    now = GROUND.storedOf(STACK, states).total()
    self.assertLess(abs(now + books.heat() - books.work() - held),
                    2e-3 * books.heat())

  def test_pieces(self) -> None:
    """Resting, a stack cut into pieces on its steps goes on as whole,
    its holds kept. The world steps at its bound (0.25 ms), so every
    piece takes the same steps: a call takes the longest step what can
    happen in it allows, and at 1 ms the first 0.2 s, the box unable to
    reach the ground in it, would step at 0.5 ms, the whole at 0.25."""
    states = (State((0.0, 0.0, 0.1)), State((0.05, 0.02, 0.35)))
    whole = BOUND.advancedAll(STACK, states, 0.5)
    pieces = BOUND.advancedAll(STACK, BOUND.advancedAll(STACK, states,
                                                        0.2), 0.3, 0.2)
    self.assertNear(pieces, whole, 1e-12)

  def test_carried(self) -> None:
    """A box set on the held platform comes to rest on it; the legs
    carry it with the platform."""
    rig, states = onPlatform(HELD)
    states = WORLD.advancedAll(rig, states, 1.0)
    self.assertLess(norm(states[1].velocity), 5e-3)
    self.assertEqual(len(states[1].holds), len(BOTTOM))
    pushes = WORLD.pushesOf(rig, states)
    bare = WORLD.pushesOf(Assembly((PLATE,), RIG.legs(PLATE, 0, HELD)),
                          states[:1])
    share = (PLATE.mass + BOX.mass) / PLATE.mass
    self.assertAlmostEqual(sum(pushes) / sum(bare), share, 2)

  def test_tilted(self) -> None:
    """Rolled to 20 degrees, gentler than its grip (26.6 at 0.5), the box
    stays put on the platform; to 35, it slides off down the slope."""
    for degrees, slides in ((20.0, False), (35.0, True)):
      motion = SwayingPose(HELD.place, UNTURNED, ORIGIN,
                           (math.radians(degrees), 0.0, 0.0), 0.25)
      rig, states = onPlatform(motion)
      states = WORLD.advancedAll(rig, states, 0.3)
      before = rotated(conjugate(states[0].turn),
                       minus(states[1].place, states[0].place))
      states = WORLD.advancedAll(rig, states, 0.7, 0.3)
      after = rotated(conjugate(states[0].turn),
                      minus(states[1].place, states[0].place))
      moved = norm(minus(after, before))
      if slides:
        self.assertGreater(moved, 0.05)
      else:
        self.assertLess(moved, 1e-3)

  def test_heaved(self) -> None:
    """Heaved 1 cm at 3 Hz (pulled down at most 0.36 g) the box, set
    riding along, never lets go; at 6 Hz (1.45 g) it hops."""
    rig, settled = onPlatform(HELD)
    settled = WORLD.advancedAll(rig, settled, 0.3)
    for frequency, hops in ((3.0, False), (6.0, True)):
      motion = SwayingPose(HELD.place, UNTURNED, (0.0, 0.0, 0.01), ORIGIN,
                           frequency)
      rig, _ = onPlatform(motion)
      box = settled[1]
      riding = motion.at(0.0).velocity
      states = (motion.at(0.0).state(),
                State(box.place, box.turn, riding, ORIGIN, box.bristles,
                      box.holds))
      let = False
      for step in range(50):
        states = WORLD.advancedAll(rig, states, 0.01, 0.01 * step)
        let = let or not states[1].holds
      self.assertEqual(let, hops)

  def test_welded(self) -> None:
    """Two boxes welded side by side, touching, with a contact between
    them, do not push each other: they move as one."""
    left = State((-0.15, 0.0, 0.0), UNTURNED, (1.0, 0.0, 0.0),
                 (0.0, 0.0, 1.0))
    right = State((0.15, 0.0, 0.0), UNTURNED, (1.0, 0.3, 0.0),
                  (0.0, 0.0, 1.0))
    welded = Assembly((BOX, BOX), (Weld((0, 1)), Contact(0, 1)))
    plain = Assembly((BOX, BOX), (Weld((0, 1)),))
    space = World((0.0, 0.0, 0.0), 1e-3)
    self.assertNear(space.advancedAll(welded, (left, right), 0.5),
                    space.advancedAll(plain, (left, right), 0.5), 0.0)
