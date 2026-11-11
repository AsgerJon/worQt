"""
TestStone covers 'Stone', one stone of the aggregate: a convex polyhedron,
corners drawn at random about an ellipsoid longer than it is wide and
wider than it is thick, as stones are, turned at random, and as large by
volume as the sphere of its size. Cut by a plane it shows as a convex
polygon.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
import torch

from worQt.engineering.meso import Stone

from . import MesoTest


def _area(polygon: torch.Tensor) -> float:
  """The area of a polygon, its corners in order."""
  x, y = polygon[:, 0], polygon[:, 1]
  return 0.5 * (x * torch.roll(y, -1) - torch.roll(x, -1) * y).sum().item()


class TestStone(MesoTest):
  """Tests for 'Stone'."""

  def setUp(self) -> None:
    super().setUp()
    self.stone = Stone.random(numpy.random.default_rng(11), 8.0)

  def test_as_large_as_its_size(self) -> None:
    """A stone is as large by volume as the sphere of its size."""
    stone = self.stone
    self.assertEqual(stone.size, 8.0)
    wanted = math.pi / 6 * 8.0 ** 3
    self.assertAlmostEqual(stone.volume / wanted, 1.0, delta=1e-9)

  def test_convex(self) -> None:
    """Every corner is within every face, and the centre well inside,
    'inner' from the nearest face and 'outer' from the farthest
    corner."""
    stone = self.stone
    reach = stone.vertices @ stone.normals.T - stone.offsets
    self.assertLessEqual(reach.max().item(), 1e-9)
    self.assertGreater(stone.inner, 0.0)
    self.assertGreater(stone.outer, stone.inner)
    far = stone.vertices.norm(dim=1).max().item()
    self.assertAlmostEqual(stone.outer, far)
    self.assertAlmostEqual(stone.normals.norm(dim=1).min().item(), 1.0)

  def test_stone_shaped(self) -> None:
    """Longer than wide and wider than thick, but no flake: its longest
    extent at most about three times its shortest."""
    for seed in range(40):
      stone = Stone.random(numpy.random.default_rng(seed), 8.0)
      spread = stone.vertices - stone.vertices.mean(0)
      _, values, axes = torch.linalg.svd(spread, False)
      extents = (spread @ axes.T).abs().amax(0)
      ratio = (extents.max() / extents.min()).item()
      self.assertGreater(ratio, 1.05)
      self.assertLess(ratio, 3.3)

  def test_turned_at_random(self) -> None:
    """Stones are turned every way: the longest axes of many point
    along x as much as a random direction does, a half on average."""
    along = []
    for seed in range(300):
      stone = Stone.random(numpy.random.default_rng(seed), 8.0)
      spread = stone.vertices - stone.vertices.mean(0)
      axes = torch.linalg.svd(spread, False)[2]
      along.append(abs(axes[0, 0].item()))
    self.assertAlmostEqual(sum(along) / len(along), 0.5, delta=0.05)

  def test_the_same_stone(self) -> None:
    """The same draw makes the same stone."""
    again = Stone.random(numpy.random.default_rng(11), 8.0)
    self.assertTrue(torch.equal(self.stone.vertices, again.vertices))

  def test_moved(self) -> None:
    """A stone moved keeps its shape; its corners are where it is."""
    centre = torch.tensor([1.0, 2.0, 3.0]).double()
    moved = self.stone.moved(centre)
    self.assertTrue(torch.equal(moved.vertices, self.stone.vertices))
    self.assertTrue(torch.equal(moved.corners - centre, moved.vertices))

  def test_the_section(self) -> None:
    """Cut through its centre, a stone shows as a convex polygon, its
    corners in order round it, within the stone; cut beyond its reach,
    it shows nothing."""
    stone = self.stone
    polygon = stone.section(0.0)
    self.assertGreaterEqual(len(polygon), 3)
    self.assertGreater(_area(polygon), 0.0)
    turns = []
    count = len(polygon)
    for index in range(count):
      one = polygon[(index + 1) % count] - polygon[index]
      two = polygon[(index + 2) % count] - polygon[(index + 1) % count]
      turns.append((one[0] * two[1] - one[1] * two[0]).item())
    self.assertGreater(min(turns), 0.0)
    points = torch.cat([polygon, torch.zeros(count, 1).double()], 1)
    reach = points @ stone.normals.T - stone.offsets
    self.assertLessEqual(reach.max().item(), 1e-9)
    self.assertIsNone(stone.section(stone.outer + 0.1))

  def test_the_sections_add_up(self) -> None:
    """Its sections, plane by plane, add up to its volume."""
    stone = self.stone
    planes = 1600
    depth = 2 * stone.outer / planes
    total = 0.0
    for index in range(planes):
      polygon = stone.section(-stone.outer + (index + 0.5) * depth)
      if polygon is not None:
        total += _area(polygon) * depth
    self.assertAlmostEqual(total / stone.volume, 1.0, delta=0.002)
