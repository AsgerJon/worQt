"""
TestCylinder covers 'Cylinder', a concrete cylinder as it is cast: its
stones, the grading's from the smallest stone modelled up, each a
'Stone' turned at random, placed at random one by one, largest first,
wholly inside the mould and never overlapping, in the slab either side
of the section through the axis, 1.5 largest sizes deep, which is all
the stones the section can meet and all those that could stand in their
way.

Cut by a plane, the stones show as convex polygons; added up plane by
plane, the polygons make up the stones' volume again.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch

from worQt.engineering.meso import Cylinder, Grading, Stone, WholeCylinder

from . import MesoTest, smallCylinder


def _area(polygon: torch.Tensor) -> float:
  """The area of a polygon, its corners in order."""
  x, y = polygon[:, 0], polygon[:, 1]
  return 0.5 * (x * torch.roll(y, -1) - torch.roll(x, -1) * y).sum().item()


def _apart(one: torch.Tensor, two: torch.Tensor,
           axes: torch.Tensor, ) -> bool:
  """Whether the corners 'one' and 'two' are apart along any of 'axes',
  touching counting as apart."""
  first, second = one @ axes.T, two @ axes.T
  gaps = torch.maximum(second.amin(0) - first.amax(0),
                       first.amin(0) - second.amax(0))
  return bool(gaps.max() >= -1e-9)


def _stonesApart(one: Stone, two: Stone) -> bool:
  """Whether two stones are apart: some face of either, or some line
  square to an edge of each, separates them."""
  edgesOne = one.vertices[one.edges[:, 1]] - one.vertices[one.edges[:, 0]]
  edgesTwo = two.vertices[two.edges[:, 1]] - two.vertices[two.edges[:, 0]]
  crossed = torch.cross(edgesOne[:, None].expand(-1, len(edgesTwo), -1),
                        edgesTwo[None].expand(len(edgesOne), -1, -1), 2)
  crossed = crossed.reshape(-1, 3)
  length = crossed.norm(dim=1)
  crossed = crossed[length > 1e-9] / length[length > 1e-9][:, None]
  axes = torch.cat([one.normals, two.normals, crossed])
  return _apart(one.corners, two.corners, axes)


def _polygonsApart(one: torch.Tensor, two: torch.Tensor) -> bool:
  """Whether two convex polygons are apart: square to some edge of
  either."""
  axes = []
  for polygon in (one, two):
    along = torch.roll(polygon, -1, 0) - polygon
    axes.append(torch.stack([along[:, 1], -along[:, 0]], 1))
  axes = torch.cat(axes)
  axes = axes / axes.norm(dim=1, keepdim=True)
  return _apart(one, two, axes)


class TestCylinder(MesoTest):
  """Tests for 'Cylinder'."""

  def setUp(self) -> None:
    super().setUp()
    self.cylinder = smallCylinder(7)

  def test_the_cast(self) -> None:
    """The cylinder keeps its size, grading and seed; the slab is 1.5
    largest sizes either side of the section; its stones are stones."""
    cylinder = self.cylinder
    self.assertEqual(cylinder.diameter, 40.0)
    self.assertEqual(cylinder.height, 80.0)
    self.assertEqual(cylinder.radius, 20.0)
    self.assertEqual(cylinder.grading.maxSize, 8.0)
    self.assertEqual(cylinder.seed, 7)
    self.assertEqual(cylinder.smallest, 4.0)
    self.assertEqual(cylinder.slabHalf, 12.0)
    self.assertGreater(len(cylinder.stones), 50)
    self.assertIsInstance(cylinder.stones[0], Stone)
    self.assertEqual(cylinder.centres.shape, (len(cylinder.stones), 3))

  def test_largest_first(self) -> None:
    """The stones are placed largest first."""
    sizes = [stone.size for stone in self.cylinder.stones]
    self.assertEqual(sizes, sorted(sizes, reverse=True))

  def test_inside_the_mould(self) -> None:
    """Every corner of every stone is inside the mould, and every centre
    in the slab."""
    for stone in self.cylinder.stones:
      corners = stone.corners
      reach = corners[:, 0] ** 2 + corners[:, 2] ** 2
      self.assertLessEqual(reach.max().item(), 400.0 + 1e-9)
      self.assertGreaterEqual(corners[:, 1].min().item(), -1e-9)
      self.assertLessEqual(corners[:, 1].max().item(), 80.0 + 1e-9)
      self.assertLessEqual(abs(stone.centre[2].item()), 12.0)

  def test_no_two_overlap(self) -> None:
    """No two stones overlap."""
    stones = self.cylinder.stones
    centres = self.cylinder.centres
    outer = torch.tensor([stone.outer for stone in stones]).double()
    gaps = torch.cdist(centres, centres) - outer[:, None] - outer[None]
    near = torch.nonzero(torch.triu((gaps < 0).double(), 1))
    self.assertGreater(len(near), 0)
    for one, two in near.tolist():
      self.assertTrue(_stonesApart(stones[one], stones[two]))

  def test_the_volume(self) -> None:
    """The stones fill the share of the slab the grading gives them:
    seven tenths of concrete is aggregate, and of that the share from
    the smallest stone up; none had to be left out."""
    cylinder = self.cylinder
    grading = cylinder.grading
    wanted = 0.7 * (1 - grading.passingAt(4.0))
    share = cylinder.stoneVolume / cylinder.slabVolume
    self.assertAlmostEqual(share / wanted, 1.0, delta=0.03)
    self.assertEqual(cylinder.skipped, 0)
    total = sum(stone.volume for stone in cylinder.stones)
    self.assertAlmostEqual(cylinder.stoneVolume, total)

  def test_the_slab_volume(self) -> None:
    """The slab is the part of the cylinder within 'slabHalf' of the
    section; a slab as deep as the cylinder is the whole cylinder."""
    deep = Cylinder(40.0, 80.0, Grading.fuller(16.0, 0.5), 7)
    self.assertEqual(deep.slabHalf, 20.0)
    self.assertAlmostEqual(deep.slabVolume, math.pi * 400 * 80)
    half, radius = 12.0, 20.0
    area = 2 * (half * math.sqrt(radius ** 2 - half ** 2)
                + radius ** 2 * math.asin(half / radius))
    self.assertAlmostEqual(self.cylinder.slabVolume, area * 80.0)

  def test_a_whole_cylinder(self) -> None:
    """A whole cylinder is cast through and through, as deep as it is
    wide, so all of it can be seen through clear paste; the stones fill
    its share of it, wholly inside the mould."""
    whole = WholeCylinder(40.0, 80.0, Grading.fuller(8.0, 0.5), 7)
    self.assertEqual(whole.slabHalf, 20.0)
    self.assertAlmostEqual(whole.slabVolume, math.pi * 400 * 80)
    wanted = 0.7 * (1 - whole.grading.passingAt(4.0))
    share = whole.stoneVolume / whole.slabVolume
    self.assertAlmostEqual(share / wanted, 1.0, delta=0.03)
    for stone in whole.stones:
      corners = stone.corners
      reach = corners[:, 0] ** 2 + corners[:, 2] ** 2
      self.assertLessEqual(reach.max().item(), 400.0 + 1e-9)
    self.assertGreater(len(whole.stones), len(self.cylinder.stones))

  def test_the_same_cast(self) -> None:
    """The same seed casts the same cylinder; another seed another."""
    again = smallCylinder(7)
    other = smallCylinder(8)
    self.assertTrue(torch.equal(self.cylinder.centres, again.centres))
    first = self.cylinder.centres[:5]
    self.assertFalse(torch.equal(first, other.centres[:5]))

  def test_the_section(self) -> None:
    """The section through the axis shows the stones it cuts as convex
    polygons, all in the section, none overlapping another."""
    polygons = self.cylinder.section(0.0)
    self.assertGreater(len(polygons), 10)
    for polygon in polygons:
      self.assertGreater(_area(polygon), 0.0)
      self.assertLessEqual(polygon[:, 0].abs().max().item(), 20.0 + 1e-9)
      self.assertGreaterEqual(polygon[:, 1].min().item(), -1e-9)
      self.assertLessEqual(polygon[:, 1].max().item(), 80.0 + 1e-9)
    for index, one in enumerate(polygons):
      for two in polygons[index + 1:]:
        self.assertTrue(_polygonsApart(one, two))

  def test_sections_add_up(self) -> None:
    """The polygons' areas, plane by plane through the slab, add up to
    the stones' volume."""
    cylinder = self.cylinder
    reach = max(stone.outer for stone in cylinder.stones)
    planes = 800
    depth = 2 * (cylinder.slabHalf + reach) / planes
    total = 0.0
    for index in range(planes):
      z = -cylinder.slabHalf - reach + (index + 0.5) * depth
      total += sum(_area(polygon) for polygon in cylinder.section(z))
    total *= depth
    self.assertAlmostEqual(total / cylinder.stoneVolume, 1.0, delta=0.002)
