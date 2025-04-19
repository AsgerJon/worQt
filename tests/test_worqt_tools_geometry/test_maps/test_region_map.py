"""TestRegionMap tests the RegionMap class."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import cos, sin, pi

from .. import AbstractTest
from worQt.tools.geometry import RegionMap

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class TestRegion(AbstractTest):
  """TestRegionMap tests the RegionMap class."""

  def setUp(self) -> None:
    """Set up the test case."""
    regionsMaps = [RegionMap(*self.randRegions()) for _ in range(100)]
    regionSizeMaps = [RegionMap(*self.randRegionSize()) for _ in range(100)]
    sizeRegionMaps = [RegionMap(*self.randSizeRegion()) for _ in range(100)]
    regionMaps = [RegionMap(self.randRegion()) for _ in range(100)]
    sizeMaps = [RegionMap(self.randSize()) for _ in range(100)]
    self.maps = [
        *regionsMaps,
        *regionSizeMaps,
        *sizeRegionMaps,
        *regionMaps,
        *sizeMaps,
    ]

  def test_region(self, ) -> None:
    """Test that RegionMap correctly moves regions. """
    for regionMap in self.maps:
      region = self.randRegion()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(region)

      unitLeft = (region.left - source.left) / source.width
      unitTop = (region.top - source.top) / source.height
      unitRight = (source.right - region.right) / source.width
      unitBottom = (source.bottom - region.bottom) / source.height

      expectedLeft = target.left + unitLeft * target.width
      expectedTop = target.top + unitTop * target.height
      expectedRight = target.right - unitRight * target.width
      expectedBottom = target.bottom - unitBottom * target.height

      self.assertAlmostEqual(actual.left, expectedLeft)
      self.assertAlmostEqual(actual.top, expectedTop)
      self.assertAlmostEqual(actual.right, expectedRight)
      self.assertAlmostEqual(actual.bottom, expectedBottom)

  def test_point(self, ) -> None:
    """Test that RegionMap correctly moves points. """
    for regionMap in self.maps:
      point = self.randPoint()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(point)

      unitX = (point.x - source.left) / source.width
      unitY = (point.y - source.top) / source.height

      expectedX = target.left + unitX * target.width
      expectedY = target.top + unitY * target.height

      self.assertAlmostEqual(actual.x, expectedX)
      self.assertAlmostEqual(actual.y, expectedY)

  def test_int_int(self, ) -> None:
    """Test that RegionMap correctly moves integer-valued points. """
    for regionMap in self.maps:
      point = self.randInts()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(*point)

      unitX = (point[0] - source.left) / source.width
      unitY = (point[1] - source.top) / source.height

      expectedX = target.left + unitX * target.width
      expectedY = target.top + unitY * target.height

      self.assertAlmostEqual(actual[0], expectedX)
      self.assertAlmostEqual(actual[1], expectedY)

  def test_int_float(self, ) -> None:
    """Test that RegionMap correctly moves mixed type points. """
    for regionMap in self.maps:
      point = self.randFloatInt()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(*point)

      unitX = (point[0] - source.left) / source.width
      unitY = (point[1] - source.top) / source.height

      expectedX = target.left + unitX * target.width
      expectedY = target.top + unitY * target.height

      self.assertAlmostEqual(actual[0], expectedX)
      self.assertAlmostEqual(actual[1], expectedY)

  def test_float_int(self, ) -> None:
    """Test that RegionMap correctly moves mixed type points. """
    for regionMap in self.maps:
      point = self.randIntFloat()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(*point)

      unitX = (point[0] - source.left) / source.width
      unitY = (point[1] - source.top) / source.height

      expectedX = target.left + unitX * target.width
      expectedY = target.top + unitY * target.height

      self.assertAlmostEqual(actual[0], expectedX)
      self.assertAlmostEqual(actual[1], expectedY)

  def test_float_float(self, ) -> None:
    """Test that RegionMap correctly moves float-valued points. """
    for regionMap in self.maps:
      point = self.randFloats()
      source = regionMap.source
      target = regionMap.target
      actual = regionMap(*point)

      unitX = (point[0] - source.left) / source.width
      unitY = (point[1] - source.top) / source.height

      expectedX = target.left + unitX * target.width
      expectedY = target.top + unitY * target.height

      self.assertAlmostEqual(actual[0], expectedX)
      self.assertAlmostEqual(actual[1], expectedY)

  def test_tuple(self) -> None:
    """Test that RegionMap correctly moves tuple-valued points. """
    randFuncs = [
        self.randInts,
        self.randFloatInt,
        self.randIntFloat,
        self.randFloats,
    ]
    for regionMap in self.maps:
      for func in randFuncs:
        point = func()
        source = regionMap.source
        target = regionMap.target
        actual = regionMap(point)

        unitX = (point[0] - source.left) / source.width
        unitY = (point[1] - source.top) / source.height

        expectedX = target.left + unitX * target.width
        expectedY = target.top + unitY * target.height

        self.assertAlmostEqual(actual[0], expectedX)
        self.assertAlmostEqual(actual[1], expectedY)

  def test_list(self, ) -> None:
    """Test that RegionMap correctly moves list-valued points. """
    randFuncs = [
        self.randInts,
        self.randFloatInt,
        self.randIntFloat,
        self.randFloats,
    ]
    for regionMap in self.maps:
      for func in randFuncs:
        point = [*func(), ]
        source = regionMap.source
        target = regionMap.target
        actual = regionMap(point)

        unitX = (point[0] - source.left) / source.width
        unitY = (point[1] - source.top) / source.height

        expectedX = target.left + unitX * target.width
        expectedY = target.top + unitY * target.height

        self.assertAlmostEqual(actual[0], expectedX)
        self.assertAlmostEqual(actual[1], expectedY)
