"""
TestTower covers a tower on the hexapod, the tests in the test: 54
maple blocks, 3 x 1 x 0.5 inches, stacked 18 layers of 3 flat (the
short side up), each layer across the one below, on the hexapod's
platform; any block may touch any other and the platform (a contact
between every two, the edges sampled every 2 cm); in a world letting
bodies at rest sleep. Held still it stands: settled, no block moved
sideways a millimetre, the tower as tall as stacked less its give, the
legs carrying its weight; left longer every block falls asleep, still
where it was; heaved gently it wakes and rides along, standing; surged
hard it wakes and comes down.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Contact
from worQt.phys import HeldPose, Hexapod, Sleep, State, SwayingPose
from worQt.phys import World, boxShape, minus, norm, turnAbout

from . import PhysTest

INCH = 0.0254
LONG, WIDE, THICK = 3.0 * INCH, 1.0 * INCH, 0.5 * INCH
BLOCK = Body.of(boxShape(LONG, WIDE, THICK), 700.0)
PLATE = Body.of(boxShape(1.4, 1.4, 0.05), 2700.0)
RIG = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, -0.025)
HELD = HeldPose((0.0, 0.0, 1.0))
TOP = 1.025
LEVELS = 18
ACROSS = turnAbout((0.0, 0.0, 1.0), 0.5 * math.pi)
WORLD = World((0.0, 0.0, -9.81), 1e-3, None, None, True, Sleep())


def tower(motion: object) -> tuple[Assembly, tuple]:
  """The 'tower' function returns the tower on the hexapod moving as
  'motion' says, and how it starts: each layer a tenth of a millimetre
  above the one below, the blocks still. Wood on wood: 1e5 N/m per m
  of edge, damped, grip 0.4, the edges sampled every 2 cm."""
  states = [motion.at(0.0).state()]
  for level in range(LEVELS):
    z = TOP + (level + 0.5) * THICK + (level + 1) * 1e-4
    for k in range(3):
      offset = (k - 1) * WIDE
      if level % 2 == 0:
        states.append(State((0.0, offset, z)))
      else:
        states.append(State((offset, 0.0, z), ACROSS))
  count = 3 * LEVELS
  contacts = tuple(Contact(a, b, 1e5, 10.0, 0.4, 1e5, 100.0, 0.02)
                   for a in range(count + 1)
                   for b in range(a + 1, count + 1))
  bodies = (PLATE,) + (BLOCK,) * count
  return (Assembly(bodies, RIG.legs(PLATE, 0, motion) + contacts),
          tuple(states))


def riding(settled: tuple, motion: object) -> tuple:
  """The 'riding' function returns the 'settled' tower set moving with
  the platform as 'motion' starts it, asleep as it was (the platform
  moving wakes it)."""
  moving = motion.at(0.0).velocity
  return (motion.at(0.0).state(),) + tuple(
    State(block.place, block.turn, moving, block.spin, block.bristles,
          block.holds, block.rest) for block in settled[1:])


class TestTower(PhysTest):
  """Tests for the tower on the hexapod."""

  @classmethod
  def setUpClass(cls) -> None:
    """Stacks the tower on the held hexapod and lets it settle half a
    second, then half a second more, in which it falls asleep."""
    super().setUpClass()
    cls.rig, cls.stacked = tower(HELD)
    cls.settled = WORLD.advancedAll(cls.rig, cls.stacked, 0.5)
    cls.slept = WORLD.advancedAll(cls.rig, cls.settled, 0.5, 0.5)

  def test_stands(self) -> None:
    """Settled, no block has moved sideways a millimetre; the tower is
    as tall as stacked less a few millimetres' give; the legs carry its
    weight, within a tenth (it is still settling)."""
    for block, start in zip(self.settled[1:], self.stacked[1:]):
      sideways = math.hypot(block.place[0] - start.place[0],
                            block.place[1] - start.place[1])
      self.assertLess(sideways, 1e-3)
    height = max(block.place[2] for block in self.settled[1:]) + (
      0.5 * THICK) - TOP
    self.assertLess(height, LEVELS * THICK)
    self.assertGreater(height, LEVELS * THICK - 0.003)
    lifted = 0.0
    for leg, push in zip(self.rig.actuators,
                         WORLD.pushesOf(self.rig, self.settled, 0.5)):
      head = PLATE.placeOf(self.settled[0], leg.secondPoint)
      along = minus(head, leg.firstPoint)
      lifted += push * along[2] / norm(along)
    weight = 3 * LEVELS * BLOCK.mass * 9.81
    self.assertLess(abs((lifted - PLATE.mass * 9.81) / weight - 1.0), 0.1)

  def test_sleeps(self) -> None:
    """Left half a second more, every block falls asleep, none having
    moved a hundredth of a millimetre; the platform, on its legs, never
    does."""
    for block, settled in zip(self.slept[1:], self.settled[1:]):
      self.assertGreaterEqual(block.rest, Sleep().settle)
      self.assertEqual(block.velocity, (0.0, 0.0, 0.0))
      self.assertLess(norm(minus(block.place, settled.place)), 1e-5)
    self.assertEqual(self.slept[0].rest, 0.0)

  def test_rides(self) -> None:
    """Heaved 2 mm at 2 Hz (0.03 g), the sleeping tower wakes, every
    block, and rides along standing: no block moves sideways a
    millimetre, the top stays up."""
    motion = SwayingPose(HELD.place, UNTURNED, (0.0, 0.0, 0.002), ORIGIN,
                         2.0)
    rig, _ = tower(motion)
    states = WORLD.advancedAll(rig, riding(self.slept, motion), 0.5)
    for block in states[1:]:
      self.assertEqual(block.rest, 0.0)
    for block, start in zip(states[1:], self.slept[1:]):
      sideways = math.hypot(block.place[0] - start.place[0],
                            block.place[1] - start.place[1])
      self.assertLess(sideways, 1e-3)
    self.assertGreater(max(block.place[2] for block in states[1:]),
                       TOP + LEVELS * THICK - 0.01)

  def test_topples(self) -> None:
    """Surged 5 cm at 2.5 Hz (1.3 g sideways, three times the grip), the
    sleeping tower wakes and comes down: within a second its top is
    lower than a third of its height."""
    motion = SwayingPose(HELD.place, UNTURNED, (0.05, 0.0, 0.0), ORIGIN,
                         2.5)
    rig, _ = tower(motion)
    states = WORLD.advancedAll(rig, riding(self.slept, motion), 1.0)
    self.assertLess(max(block.place[2] for block in states[1:]),
                    TOP + LEVELS * THICK / 3.0)
