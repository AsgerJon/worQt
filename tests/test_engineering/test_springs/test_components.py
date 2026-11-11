"""
TestComponents covers the components and the guides of a 'System': a
'SpringMassDamper' is a rod, rigid but for its length; fixed, its mass
bobs along it only, at sqrt(k / m); hinged, it bobs and swings in the
plane square to its hinge, as a pendulum as long; free, it is a spring
pendulum. A point moves along the axes it may: a cart on a rail with a
pendulum hinged on it drifts, and swings at sqrt(g / L (M + m) / M).
The guides hold as it moves. A component is made only as it can be.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.springs import Motion, Point, Spring
from worQt.engineering.springs import SpringMassDamper, System

from . import SpringsTest

_G = 9.81


def _hz(omega: float) -> float:
  """'omega', in rad/s, in Hz."""
  return omega / (2 * math.pi)


def _hanging(turning: str) -> System:
  """A mass of 2 kg hanging a metre under an anchor, at the end of a
  component of 50 N/m turning as 'turning' says, hinged about y."""
  points = (Point((0.0, 0.0, 3.0), 1.0, ''),
            Point((0.0, 0.0, 2.0), 2.0, 'xyz'))
  rod = SpringMassDamper(0, 1, 50.0, 0.0, 1.0, turning, (0.0, 1.0, 0.0))
  return System(points, (), (), (rod,))


def _cart(stiffness: float) -> System:
  """A cart of 3 kg on a rail along x, a pendulum of 1 kg a metre under
  it, hinged about y, its rod of 'stiffness'."""
  points = (Point((0.0, 0.0, 2.0), 3.0, 'x'),
            Point((0.0, 0.0, 1.0), 1.0, 'xyz'))
  rod = SpringMassDamper(0, 1, stiffness, 0.0, 1.0, 'hinge',
                         (0.0, 1.0, 0.0))
  return System(points, (), (), (rod,))


class TestComponents(SpringsTest):
  """Tests for the components and the guides of 'System'."""

  def test_fixed(self) -> None:
    """Fixed, the mass rests m g / k down the rod and bobs along it
    only, at sqrt(k / m)."""
    system = _hanging('fixed')
    rest = system.rest()
    self.assertAlmostEqual(float(rest[1, 2]), 2.0 - 2 * _G / 50)
    frequencies, shapes = system.modes()
    self.assertEqual(len(frequencies), 1)
    self.assertAlmostEqual(frequencies[0], _hz(5.0), 9)
    self.assertAlmostEqual(float(shapes[0, 1, :2].abs().max()), 0.0)

  def test_hinged(self) -> None:
    """Hinged, it swings in the plane square to its hinge as a pendulum
    as long, and bobs."""
    frequencies, shapes = _hanging('hinge').modes()
    length = 1.0 + 2 * _G / 50
    self.assertEqual(len(frequencies), 2)
    self.assertAlmostEqual(frequencies[0], _hz(math.sqrt(_G / length)), 9)
    self.assertAlmostEqual(frequencies[1], _hz(5.0), 9)
    self.assertAlmostEqual(float(shapes[:, 1, 1].abs().max()), 0.0)

  def test_free(self) -> None:
    """Free, it swings either way and bobs, a spring pendulum."""
    frequencies, _ = _hanging('free').modes()
    self.assertEqual(len(frequencies), 3)
    spring = System(_hanging('free').points,
                    (Spring(0, 1, 50.0, 1.0),), ())
    for value, other in zip(frequencies, spring.modes()[0]):
      self.assertAlmostEqual(value, other, 9)

  def test_cart(self) -> None:
    """A cart on a rail drifts, a mode of nought, and the pendulum on it
    swings at sqrt(g / L (M + m) / M), L the rod's length as it hangs."""
    stiffness = 1e5
    frequencies, _ = _cart(stiffness).modes()
    length = 1.0 + _G / stiffness
    swing = math.sqrt(_G / length * 4.0 / 3.0)
    self.assertAlmostEqual(frequencies[0], 0.0, 6)
    self.assertAlmostEqual(frequencies[1], _hz(swing), 9)

  def test_guides_hold(self) -> None:
    """Moving, the cart keeps to its rail and the pendulum to its plane,
    and the energy stays what it began as."""
    points = (Point((0.0, 0.0, 2.0), 3.0, 'x'),
              Point((0.3, 0.0, 1.1), 1.0, 'xyz'))
    rod = SpringMassDamper(0, 1, 200.0, 0.0, 1.0, 'hinge',
                           (0.0, 1.0, 0.0))
    motion = Motion(System(points, (), (), (rod,)))
    for _ in range(600):
      motion.advance(1 / 60)
    places = motion.positions
    self.assertLess(float(places[:, 1].abs().max()), 1e-12)
    self.assertAlmostEqual(float(places[0, 2]), 2.0, 12)
    self.assertNotAlmostEqual(float(places[0, 0]), 0.0)
    totals = [sample.energies.total for sample in motion.samples]
    self.assertLess(max(totals) - min(totals), 1e-3)

  def test_refused(self) -> None:
    """A component joins two points there are, its tip away from its
    base, turning fixed, hinged or free, a hinge's axis across it; a
    point moves along x, y or z."""
    points = _hanging('fixed').points
    cases = (
      (SpringMassDamper(0, 0, 1.0, 0.0, 1.0, 'fixed', (0, 1, 0)),
       'not P1 to itself'),
      (SpringMassDamper(0, 1, 1.0, 0.0, 1.0, 'wobbly', (0, 1, 0)),
       "not 'wobbly'"),
      (SpringMassDamper(0, 1, 1.0, 0.0, 1.0, 'hinge', (0, 0, 1)),
       'along the rod'),
      (SpringMassDamper(0, 1, 0.0, 0.0, 1.0, 'fixed', (0, 1, 0)),
       'stiff'),
    )
    for rod, words in cases:
      with self.assertRaises(ValueError) as context:
        System(points, (), (), (rod,))
      self.assertIn(words, str(context.exception))
    with self.assertRaises(ValueError):
      System((Point((0.0, 0.0, 0.0), 1.0, 'xw'),), (), ())

  def test_without_point(self) -> None:
    """A point taken away takes its components along; a component taken
    away leaves its points."""
    system = _hanging('hinge')
    self.assertEqual(system.withoutPoint(1).components, ())
    self.assertEqual(len(system.withoutComponent(0).points), 2)
