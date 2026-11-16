"""
TestItem covers what the GUI spawns ('Item', 'ITEMS'): a ball and a
crate, each spawned still where asked, drawn in its own look, falling
onto the island and resting there.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.gaming.sandbox import ITEMS

from . import SandboxTest
from ._islandworld import TOP


class TestItem(SandboxTest):
  """Tests for the items (seconds)."""

  def test_items(self) -> None:
    """A ball and a crate there are to spawn."""
    self.assertEqual([item.name for item in ITEMS], ['Ball', 'Crate'])

  def test_spawned(self) -> None:
    """Each spawned a metre over the island lands and rests on it, drawn
    in its look."""
    world, _ = self.islandWorld()
    rests = {}
    for item, x, half in zip(ITEMS, (-5.0, -4.0), (0.15, 0.25)):
      index = item.spawned(world, (x, 0.0, TOP + 1.0))
      look = world.drawn[index]
      self.assertEqual(world.looks[look], item.look)
      rests[index] = TOP + half
    self.ran(world, 2.0)
    for index, height in rests.items():
      with self.subTest(index=index):
        self.assertAlmostEqual(world.states[index].place[2], height, 2)
