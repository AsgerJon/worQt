"""
TestUniverse covers the universe's constants ('Universe'): gravity pulls
straight down, never up; a ball in the moon's world falls as the moon
pulls it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import EARTH_GRAVITY, MOON_GRAVITY, Universe
from worQt.phys._body import Body, State
from worQt.phys._shape import Sphere

from . import SandboxTest
from ._islandworld import IslandWorld


class TestUniverse(SandboxTest):
  """Tests for the universe."""

  def test_gravity(self) -> None:
    """Gravity is straight down, m/s²."""
    self.assertEqual(Universe(EARTH_GRAVITY).gravityVector(),
                     (0.0, 0.0, -9.81))
    self.assertEqual(Universe(MOON_GRAVITY).gravity, 1.62)

  def test_refused(self) -> None:
    """Gravity pulling up is refused."""
    with self.assertRaises(ValueError):
      Universe(-1.0)

  def test_moon(self) -> None:
    """A ball let go 10 m over the moon's island falls 'MOON_GRAVITY'
    m/s faster each second."""
    world = IslandWorld(Universe(MOON_GRAVITY))
    state = State((0.0, 0.0, 10.0))
    index = world.spawned(Body.of(Sphere(0.15), 700.0), state,
                          (1e6, 1.0, 0.6, 1e6, 2e3), 'dirt')
    self.ran(world, 0.5)
    self.assertAlmostEqual(world.states[index].velocity[2],
                           -0.5 * MOON_GRAVITY, 2)
