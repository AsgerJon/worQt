"""
TestHexapod covers 'Hexapod', a test rig, a Gough-Stewart platform: a
moving platform on six actuators from the ground, their strokes
('LegStroke') worked out from the motion it is to make ('HeldPose',
'SwayingPose'). Its feet and heads lie on their circles, in zigzagging
pairs; a leg's rate and its growth are its length's own, as differences
say; held, the six legs push alike, together the platform's weight, and
it stays put; it follows heave, roll with surge, and yaw to a hair. Then
the tests in the test: a block on a spring and a damper hung under it,
heaved, swings at the transmissibility by hand, the books balancing the
legs' work; a cube tied at its middle to the platform's turns not at all
however the platform rolls and yaws; a load hung from it adds its weight
to the legs. Its feet may stand round a middle of their own: the same
legs, their feet moved over the ground to it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import ORIGIN, UNTURNED, Assembly, Body, Books, Damper
from worQt.phys import HeldPose, Hexapod, Spring, State
from worQt.phys import SwayingPose, Tie, World, boxShape, minus, norm
from worQt.phys import scaled

from . import PhysTest

WORLD = World()
PLATE = Body.of(boxShape(1.4, 1.4, 0.05), 2700.0)
RIG = Hexapod(1.0, 0.6, 20.0, 20.0, 0.0, -0.025)
MIDDLE = (0.0, 0.0, 1.0)
HELD = HeldPose(MIDDLE)
BLOCK = Body.of(boxShape(0.2, 0.2, 0.2), 1000.0)
SAG = BLOCK.mass * 9.81 / 800.0


def legForces(assembly: Assembly, states: tuple) -> tuple:
  """The 'legForces' function returns the force each leg of the rig in
  'assembly' puts on the platform (its first body), N, in the world."""
  out = []
  for leg, push in zip(assembly.actuators,
                       WORLD.pushesOf(assembly, states)):
    head = PLATE.placeOf(states[0], leg.secondPoint)
    along = minus(head, leg.firstPoint)
    out.append(scaled(along, push / norm(along)))
  return tuple(out)


class TestHexapod(PhysTest):
  """Tests for 'Hexapod' and what it carries."""

  def test_geometry(self) -> None:
    """The feet stand on their circle on the ground, the heads on
    theirs under the platform, each pair its spread apart; at a level
    pose over the middle every leg is as long."""
    feet, heads = RIG.feet(), RIG.heads()
    for foot, head in zip(feet, heads):
      self.assertAlmostEqual(norm(foot), 1.0, 14)
      self.assertAlmostEqual(math.hypot(head[0], head[1]), 0.6, 14)
      self.assertEqual(foot[2], 0.0)
      self.assertEqual(head[2], -0.025)
    for pair in range(3):
      apart = math.atan2(feet[2 * pair + 1][1], feet[2 * pair + 1][0]) - (
        math.atan2(feet[2 * pair][1], feet[2 * pair][0]))
      self.assertAlmostEqual(math.degrees(apart) % 360.0, 20.0, 9)
    lengths = [leg.stroke.at(0.0)[0] for leg in RIG.legs(PLATE, 0, HELD)]
    for length in lengths:
      self.assertAlmostEqual(length, lengths[0], 13)

  def test_stroke(self) -> None:
    """A leg's rate and how fast it grows are its length's own, as
    small differences in time say."""
    motion = SwayingPose(MIDDLE, UNTURNED, (0.03, -0.02, 0.05),
                         (0.05, 0.08, -0.1), 0.7)
    for leg in RIG.legs(PLATE, 0, motion):
      length, rate, growing = leg.stroke.at(0.3)
      before, after = leg.stroke.at(0.3 - 1e-5), leg.stroke.at(0.3 + 1e-5)
      self.assertAlmostEqual(rate, (after[0] - before[0]) / 2e-5, 8)
      self.assertAlmostEqual(growing, (after[1] - before[1]) / 2e-5, 6)

  def test_holds(self) -> None:
    """Held, the six legs push alike, together the platform's weight,
    and it stays put."""
    rig = Assembly((PLATE,), RIG.legs(PLATE, 0, HELD))
    states = (HELD.at(0.0).state(),)
    forces = legForces(rig, states)
    total = (sum(f[0] for f in forces), sum(f[1] for f in forces),
             sum(f[2] for f in forces))
    self.assertNear(total, (0.0, 0.0, PLATE.mass * 9.81), 1e-9)
    for force in forces:
      self.assertAlmostEqual(norm(force), norm(forces[0]), 9)
    later = WORLD.advancedAll(rig, states, 1.0)
    self.assertNear(later[0].place, MIDDLE, 1e-14)
    self.assertSameTurn(later[0].turn, UNTURNED, 1e-14)

  def test_follows(self) -> None:
    """Told to heave, to roll while it surges, or to yaw, the platform
    does, to a hair."""
    for motion in (SwayingPose(MIDDLE, UNTURNED, (0.0, 0.0, 0.05), ORIGIN,
                               1.0),
                   SwayingPose(MIDDLE, UNTURNED, (0.03, 0.0, 0.0),
                               (math.radians(5.0), 0.0, 0.0), 0.7),
                   SwayingPose(MIDDLE, UNTURNED, ORIGIN,
                               (0.0, 0.0, math.radians(10.0)), 0.5)):
      rig = Assembly((PLATE,), RIG.legs(PLATE, 0, motion))
      states = (motion.at(0.0).state(),)
      for step in range(50):
        states = WORLD.advancedAll(rig, states, 0.02, 0.02 * step)
        pose = motion.at(0.02 * (step + 1))
        self.assertNear(states[0].place, pose.place, 1e-12)
        self.assertSameTurn(states[0].turn, pose.turn, 1e-12)
        self.assertNear(states[0].velocity, pose.velocity, 1e-12)

  def test_shaken(self) -> None:
    """A block on a spring and a damper (half critical) hung under the
    platform, heaved at its own rate and at twice it, swings at the
    transmissibility by hand; the books balance the legs' work against
    the damper's heat and what is held."""
    rate = math.sqrt(800.0 / BLOCK.mass)
    damping = math.sqrt(800.0 * BLOCK.mass)
    for ratio in (1.0, 2.0):
      motion = SwayingPose(MIDDLE, UNTURNED, (0.0, 0.0, 0.01), ORIGIN,
                           ratio * rate / (2.0 * math.pi))
      rig = Assembly((PLATE, BLOCK), RIG.legs(PLATE, 0, motion) + (
        Spring(0, ORIGIN, 1, ORIGIN, 800.0, 0.6),
        Damper(0, ORIGIN, 1, ORIGIN, damping)))
      states = (motion.at(0.0).state(), State((0.0, 0.0, 0.4 - SAG)))
      held = WORLD.storedOf(rig, states).total()
      states, books = WORLD.booked(rig, states, 3.0, 0.0, Books())
      heights, time = [], 3.0
      for _ in range(1500):
        states, books = WORLD.booked(rig, states, 0.001, time, books)
        time += 0.001
        heights.append(states[1].place[2])
      swing = 0.5 * (max(heights) - min(heights)) / 0.01
      passed = math.sqrt((1.0 + ratio ** 2) / ((1.0 - ratio ** 2) ** 2
                                               + ratio ** 2))
      self.assertLess(abs(swing / passed - 1.0), 1e-4)
      now = WORLD.storedOf(rig, states).total()
      self.assertGreater(books.actuators, 20.0)
      self.assertLess(abs(now + books.heat() - books.work() - held), 1e-3)

  def test_tied(self) -> None:
    """A cube tied at its middle to the platform's middle is carried
    along, its middle with the platform's, turning not at all however
    the platform rolls and yaws."""
    motion = SwayingPose(MIDDLE, UNTURNED, ORIGIN,
                         (math.radians(8.0), 0.0, math.radians(10.0)), 0.5)
    rig = Assembly((PLATE, BLOCK), RIG.legs(PLATE, 0, motion) + (
      Tie(0, ORIGIN, 1, ORIGIN),))
    states = (motion.at(0.0).state(), State(MIDDLE))
    states = WORLD.advancedAll(rig, states, 1.0)
    self.assertNear(states[1].place, MIDDLE, 1e-12)
    self.assertSameTurn(states[1].turn, UNTURNED, 1e-14)
    self.assertNear(states[1].spin, ORIGIN, 1e-14)

  def test_loaded(self) -> None:
    """A block hung still from the platform on a spring adds its weight
    to the legs: each pushes as much more as the masses say."""
    bare = Assembly((PLATE,), RIG.legs(PLATE, 0, HELD))
    loaded = Assembly((PLATE, BLOCK), RIG.legs(PLATE, 0, HELD) + (
      Spring(0, ORIGIN, 1, ORIGIN, 800.0, 0.6),))
    plate = HELD.at(0.0).state()
    alone = WORLD.pushesOf(bare, (plate,))
    carrying = WORLD.pushesOf(loaded, (plate, State((0.0, 0.0, 0.4 - SAG))))
    share = (PLATE.mass + BLOCK.mass) / PLATE.mass
    for before, after in zip(alone, carrying):
      self.assertAlmostEqual(after / before, share, 12)

  def test_round_middle(self) -> None:
    """Legs with their feet round a middle stand where the feet round
    the world's origin do, moved over the ground to it, holding the
    platform's same points; each as long as from its foot to its head
    on the platform held there."""
    shifted = State((0.3, -0.2, 1.2))
    legs = RIG.legs(PLATE, 0, HeldPose(shifted.place), (0.3, -0.2))
    for leg, foot, head in zip(legs, RIG.feet(), RIG.heads()):
      self.assertNear(leg.firstPoint, (foot[0] + 0.3, foot[1] - 0.2,
                                       foot[2]), 1e-15)
      self.assertEqual(leg.secondPoint, head)
      held = (head[0] + 0.3 - PLATE.centre[0],
              head[1] - 0.2 - PLATE.centre[1],
              head[2] + 1.2 - PLATE.centre[2])
      self.assertAlmostEqual(leg.stroke.at(0.0)[0],
                             norm(minus(held, leg.firstPoint)), 12)
