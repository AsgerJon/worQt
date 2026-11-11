"""
TestMotion covers 'Motion', a system of springs moving through time: a
mass bobs as it should, damped or not; without dampers the energy stays
what it began as, and with them what the dampers turn to heat is
accounted for; a free mass falls as it should; the same motion twice is
the same; a point held is pulled along and let go moving, the hand's
work accounted for; a spring too stiff for the steps slows the motion;
a component spinning on its hinge stretches as it should.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch

from worQt.engineering.springs import Damper, Motion, Point, Spring
from worQt.engineering.springs import SpringMassDamper, System

from . import SpringsTest, hanging

_FRAME = 1 / 60


class TestMotion(SpringsTest):
  """Tests for 'Motion'."""

  def bobbing(self, system: System) -> tuple[Motion, float]:
    """'system' pulled 0.1 m down from its rest, and its rest."""
    rest = system.rest()
    start = rest.clone()
    start[1, 2] -= 0.1
    return Motion(system, start), float(rest[1, 2])

  def run(self, motion: Motion, seconds: float) -> None:
    """Moves 'motion' on 'seconds', a frame at a time."""
    for _ in range(round(seconds / _FRAME)):
      motion.advance(_FRAME)

  def test_bobbing(self) -> None:
    """Pulled down and let go, the mass bobs at sqrt(k / m), as its
    exact motion has it, ten seconds on."""
    motion, rest = self.bobbing(hanging())
    self.run(motion, 10.0)
    exact = rest - 0.1 * math.cos(5.0 * motion.time)
    self.assertAlmostEqual(motion.time, 10.0)
    self.assertLess(abs(float(motion.positions[1, 2]) - exact), 1e-4)
    self.assertLess(float(motion.positions[1, :2].abs().max()), 1e-12)

  def test_energy_kept(self) -> None:
    """Without dampers, the energy swings about what it began as, never
    drifting off, however the system swings."""
    motion = Motion(System())
    self.run(motion, 20.0)
    totals = [sample.energies.total for sample in motion.samples]
    self.assertLess(max(totals) - min(totals), 1e-3)
    self.assertGreater(motion.energies.kinetic, 0.0)

  def test_damped(self) -> None:
    """Damped, the mass bobs as its exact damped motion has it, and the
    energy it loses is the heat the damper makes."""
    system = hanging().withDampers(Damper(0, 1, 1.0))
    motion, rest = self.bobbing(system)
    start = motion.energies.total
    self.run(motion, 10.0)
    zeta = 1.0 / (2 * math.sqrt(50.0 * 2.0))
    damped = 5.0 * math.sqrt(1 - zeta ** 2)
    t = motion.time
    exact = -0.1 * math.exp(-zeta * 5.0 * t) * (
        math.cos(damped * t)
        + zeta / math.sqrt(1 - zeta ** 2) * math.sin(damped * t))
    self.assertLess(abs(float(motion.positions[1, 2]) - rest - exact),
                    1e-4)
    energies = motion.energies
    self.assertGreater(energies.dissipated, 0.2)
    self.assertLess(abs(energies.total - start), 1e-6)

  def test_falling(self) -> None:
    """A mass on nothing falls g t² / 2 in t."""
    motion = Motion(System((Point((0.0, 0.0, 5.0), 1.0, 'xyz'),), (),
                           ()))
    self.run(motion, 1.0)
    exact = 5.0 - 0.5 * 9.81 * motion.time ** 2
    self.assertAlmostEqual(float(motion.positions[0, 2]), exact, 9)

  def test_the_same_twice(self) -> None:
    """The same motion twice is the same, to the last digit."""
    first, second = Motion(System()), Motion(System())
    self.run(first, 3.0)
    self.run(second, 3.0)
    self.assertTrue(bool((first.positions == second.positions).all()))

  def test_held_and_let_go(self) -> None:
    """A point held is pulled close to where it is held; let go, it
    moves on, and the energy, with the hand's work, is what it began
    as; an anchor held does not move."""
    system = hanging()
    motion = Motion(system, system.rest())
    start = motion.energies.total
    motion.hold(1, (0.3, 0.0, 1.6))
    self.run(motion, 2.0)
    self.assertEqual(motion.held, (1,))
    place = motion.positions[1].tolist()
    for value, target in zip(place, (0.3, 0.0, 1.6)):
      self.assertLess(abs(value - target), 0.01)
    motion.release(1)
    self.assertEqual(motion.held, ())
    self.run(motion, 2.0)
    self.assertGreater(motion.energies.hand, 0.0)
    self.assertLess(abs(motion.energies.total - start), 1e-2)
    motion.hold(0, (0.0, 0.0, 3.5))
    self.run(motion, 0.5)
    self.assertEqual(motion.positions[0].tolist(), [0.0, 0.0, 3.0])

  def test_slowed(self) -> None:
    """A spring too stiff for the steps a frame takes slows the motion:
    it goes less far than asked."""
    stiff = System((Point((0.0, 0.0, 1.0), 1.0, ''),
                    Point((0.0, 0.0, 0.0), 1e-3, 'xyz')),
                   (Spring(0, 1, 1e9, 1.0),), ())
    motion = Motion(stiff)
    went = motion.advance(_FRAME)
    self.assertTrue(motion.slowed)
    self.assertLess(went, _FRAME)
    self.assertAlmostEqual(motion.time, went)
    self.assertFalse(Motion(hanging()).slowed)

  def test_spinning(self) -> None:
    """A rod hinged upright on a turntable, spun, its mass flung out,
    turns at the radius where its spring holds it: k L / (k - m w²)."""
    k, m, rest, w = 100.0, 1.0, 1.0, 5.0
    radius = k * rest / (k - m * w * w)
    points = (Point((0.0, 0.0, 0.0), 1.0, ''),
              Point((radius, 0.0, 0.0), m, 'xyz'))
    rod = SpringMassDamper(0, 1, k, 0.0, rest, 'hinge', (0.0, 0.0, 1.0))
    system = System(points, (), (), (rod,), 0.0)
    v = torch.zeros(2, 3).double()
    v[1, 1] = w * radius
    motion = Motion(system, system.positions(), v)
    self.run(motion, 5.0)
    place = motion.positions[1]
    self.assertAlmostEqual(float(place[:2].norm()), radius, 4)
    self.assertEqual(float(place[2]), 0.0)
