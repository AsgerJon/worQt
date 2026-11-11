"""
TestSystem covers 'System', masses joined by springs and dampers in
space under gravity: it is made only whole; points are taken away with
the springs on them; it comes to rest where it should, swings about it
in the modes it should, and has no rest when it falls; its stiffness is
what its forces make of a little move.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch

from worQt.engineering.springs import Damper, Point, Spring, System

from . import SpringsTest, chain, hanging


class TestSystem(SpringsTest):
  """Tests for 'System'."""

  def test_standard(self) -> None:
    """Made of nothing, it is an anchor with two masses hanging from it
    on springs, under gravity."""
    system = System()
    self.assertEqual(len(system.points), 3)
    self.assertTrue(system.points[0].pinned)
    self.assertEqual([s[:2] for s in system.springs], [(0, 1), (1, 2)])
    self.assertEqual(system.dampers, ())
    self.assertEqual(system.gravity, 9.81)
    self.assertEqual(system.positions()[2].tolist(), [0.25, 0.1, 0.7])

  def test_refused(self) -> None:
    """It is made only whole: a mass to each point, each spring and
    damper between two points there are, stiff or damping, and gravity
    pulling down."""
    points = hanging().points
    weightless = (points[0], Point((0.0, 0.0, 1.0), 0.0, 'xyz'))
    cases = (
      (weightless, (), (), 'P2 has a mass above nought'),
      (points, (Spring(0, 2, 1.0, 1.0),), (), 'not P3'),
      (points, (Spring(1, 1, 1.0, 1.0),), (), 'not P2 to itself'),
      (points, (Spring(0, 1, 0.0, 1.0),), (), 'stiff, above nought'),
      (points, (Spring(0, 1, 1.0, -1.0),), (), 'rest length'),
      (points, (), (Damper(0, 1, 0.0),), 'damping, above nought'),
    )
    for nodes, springs, dampers, words in cases:
      with self.assertRaises(ValueError) as context:
        System(nodes, springs, dampers)
      self.assertIn(words, str(context.exception))
    with self.assertRaises(ValueError):
      hanging().withGravity(-1.0)

  def test_without_point(self) -> None:
    """A point taken away takes the springs and dampers on it along, the
    points after it numbered down."""
    system = chain().withDampers(Damper(1, 3, 2.0))
    without = system.withoutPoint(1)
    self.assertEqual(len(without.points), 4)
    self.assertEqual([s[:2] for s in without.springs],
                     [(1, 2), (2, 3)])
    self.assertEqual(without.dampers, (Damper(1, 2, 2.0),))
    self.assertEqual(len(system.withoutSpring(0).springs), 3)
    self.assertEqual(system.withoutDamper(0).dampers, ())

  def test_rest(self) -> None:
    """Hanging, the mass rests m g / k below where the spring is at
    rest, the force on it nought."""
    system = hanging()
    rest = system.rest()
    self.assertAlmostEqual(float(rest[1, 2]), 3.0 - 1.0 - 2 * 9.81 / 50)
    self.assertAlmostEqual(float(rest[1, 0]), 0.0)
    push = system.forces(rest, torch.zeros_like(rest))[1]
    self.assertLess(float(push.abs().max()), 1e-8)

  def test_modes_hanging(self) -> None:
    """Hanging, it swings either way as a pendulum as long as the
    stretched spring, and bobs at sqrt(k / m); the bob's shape is
    straight up and down."""
    frequencies, shapes = hanging().modes()
    length = 1.0 + 2 * 9.81 / 50
    swing = math.sqrt(9.81 / length) / (2 * math.pi)
    bob = math.sqrt(50 / 2) / (2 * math.pi)
    for value, exact in zip(frequencies, (swing, swing, bob)):
      self.assertAlmostEqual(value, exact, 9)
    self.assertEqual(shapes.shape, (3, 2, 3))
    self.assertAlmostEqual(abs(float(shapes[2, 1, 2])), 1.0)
    self.assertAlmostEqual(float(shapes[2, 1, :2].abs().max()), 0.0)
    self.assertEqual(shapes[:, 0].abs().max().item(), 0.0)

  def test_modes_chain(self) -> None:
    """The chain stretches along its line and swings across it in the
    modes of a string of three beads."""
    frequencies, _ = chain().modes()
    along = [math.sqrt(100.0 * (2 - 2 * math.cos(j * math.pi / 4)))
             for j in (1, 2, 3)]
    across = [math.sqrt(20.0 * (2 - 2 * math.cos(j * math.pi / 4)))
              for j in (1, 2, 3)]
    exact = sorted([*across, *across, *along])
    for value, omega in zip(frequencies, exact):
      self.assertAlmostEqual(value, omega / (2 * math.pi), 9)

  def test_no_rest(self) -> None:
    """A mass on nothing falls for ever: it has no rest, and no
    modes."""
    falling = System((Point((0.0, 0.0, 5.0), 1.0, 'xyz'),), (), ())
    self.assertIsNone(falling.rest())
    self.assertIsNone(falling.modes())

  def test_tangent(self) -> None:
    """The stiffness is how the forces change as the points move a
    little, a spring turned and stretched alike."""
    system = System().withDampers(Damper(0, 2, 1.0))
    x = system.positions()
    x[1] += torch.tensor([0.1, -0.2, 0.05]).double()
    stiffness = system.tangent(x)
    still = torch.zeros_like(x)
    nudge = 1e-6
    for column in range(3 * len(system.points)):
      moved = x.clone().reshape(-1)
      moved[column] += nudge
      after = system.forces(moved.reshape(-1, 3), still).reshape(-1)
      before = system.forces(x, still).reshape(-1)
      change = -(after - before) / nudge
      for row in range(len(change)):
        self.assertAlmostEqual(float(change[row]),
                               float(stiffness[row, column]), 3)
