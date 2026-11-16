"""
TestWorld covers a world ('World', on the island's world): it holds
only its own bodies (held still) until something is spawned; a ball
spawned over the island falls onto it and rests; the world runs on its
own thread and stops; the sandbox imports nothing of the old walk
window, nor any rail (it is the general base: user, 2026-11-16).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
import time

from worQt.phys._body import Body, State
from worQt.phys._shape import Sphere

from worQt.gaming.sandbox import EARTH_GRAVITY, Universe
from worQt.gaming.sandbox._avatar import SOLES

from . import SandboxTest
from ._islandworld import TOP, IslandWorld

#  The ball dropped, its radius, m.
RADIUS = 0.15


class TestWorld(SandboxTest):
  """Tests for a world (seconds)."""

  def test_empty(self) -> None:
    """A world starts with its own bodies alone, held still and drawn,
    nothing acting in it."""
    world = IslandWorld(Universe(EARTH_GRAVITY))
    self.assertEqual(len(world.assembly.bodies), 2)
    self.assertEqual(world.still, frozenset((0, 1)))
    self.assertEqual(world.drawn, {0: 'grass', 1: 'dirt'})
    self.assertEqual(world.actors, [])
    self.assertEqual(world.fixtures(), {})

  def test_ball(self) -> None:
    """A ball spawned a metre over the island falls and rests on it."""
    world, _ = self.islandWorld()
    index = world.spawned(Body.of(Sphere(RADIUS), 700.0),
                          State((0.0, 4.0, TOP + 1.0)), SOLES, 'dirt')
    self.assertEqual(world.drawn[index], 'dirt')
    self.assertNotIn(index, world.still)
    self.ran(world, 2.0)
    state = world.states[index]
    self.assertAlmostEqual(state.place[2], TOP + RADIUS, 2)
    self.assertLess(abs(state.velocity[2]), 0.01)

  def test_thread(self) -> None:
    """Started, the world steps on its own thread; stopped, it ends."""
    world, _ = self.islandWorld()
    world.start()
    try:
      began = time.perf_counter()
      while world.time < 0.3 and time.perf_counter() - began < 60.0:
        time.sleep(0.05)
      self.assertIsNone(world.trouble)
      self.assertGreater(world.snapshot()[2], 0.3)
      with self.assertRaises(RuntimeError):
        world.advanced(0.01)
    finally:
      world.stop()
    self.assertIsNone(world.trouble)

  def test_clean(self) -> None:
    """The sandbox, window and all, imports nothing of the old walk
    window or its views, and no rail."""
    import worQt.gaming.sandbox._sandboxapp  # noqa: F401
    loaded = [name for name in sys.modules if name.startswith(
      ('worQt.phys.gui', 'worQt.phys.rail', 'worQt.gaming.trains'))]
    self.assertEqual(loaded, [])
