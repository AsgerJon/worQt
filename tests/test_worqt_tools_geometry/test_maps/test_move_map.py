"""TestMoveMap test the MoveMap class."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worQt.tools.geometry import MoveMap
from .. import AbstractTest

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class TestMoveMap(AbstractTest):
  """TestMoveMap test the MoveMap class."""

  def setUp(self, ) -> None:
    """Set up the test case."""
    floatsMaps = [MoveMap(*self.randFloats()) for _ in range(100)]
    intsMaps = [MoveMap(*self.randInts()) for _ in range(100)]
    complexMaps = [MoveMap(self.randComplex()) for _ in range(100)]
    floatMaps = [MoveMap(self.randFloat()) for _ in range(100)]
    intMaps = [MoveMap(self.randInt()) for _ in range(100)]
    pointMaps = [MoveMap(self.randPoint(), ) for _ in range(100)]
    self.maps = [
        *floatsMaps,
        *intsMaps,
        *complexMaps,
        *floatMaps,
        *intMaps,
        *pointMaps,
    ]

  def test_ints(self, ) -> None:
    """Tests that MoveMap correctly moves integers. """
    for moveMap in self.maps:
      x0, y0 = self.randInts()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = x0 + h
      y = y0 + v
      moved = moveMap(x0, y0)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_int_float(self, ) -> None:
    """Tests that MoveMap correctly moves mixed type values. """
    for moveMap in self.maps:
      x0, y0 = self.randIntFloat()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = x0 + h
      y = y0 + v
      moved = moveMap(x0, y0)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_float_int(self, ) -> None:
    """Tests that MoveMap correctly moves mixed type values. """
    for moveMap in self.maps:
      x0, y0 = self.randFloatInt()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = x0 + h
      y = y0 + v
      moved = moveMap(x0, y0)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_floats(self, ) -> None:
    """Tests that MoveMap correctly moves float values. """
    for moveMap in self.maps:
      x0, y0 = self.randFloats()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = x0 + h
      y = y0 + v
      moved = moveMap(x0, y0)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_complex(self, ) -> None:
    """Tests that MoveMap correctly moves complex values. """
    for moveMap in self.maps:
      value = self.randComplex()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = value.real + h
      y = value.imag + v
      moved = moveMap(value)
      self.assertAlmostEqual(moved.real, x)
      self.assertAlmostEqual(moved.imag, y)

  def test_point(self, ) -> None:
    """Tests that MoveMap correctly moves Point values. """
    for moveMap in self.maps:
      point = self.randPoint()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = point.x + h
      y = point.y + v
      moved = moveMap(point)
      self.assertAlmostEqual(moved.x, x)
      self.assertAlmostEqual(moved.y, y)

  def test_int(self, ) -> None:
    """Tests that MoveMap correctly moves integers"""
    for moveMap in self.maps:
      value = self.randInt()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = value + h
      y = value + v
      moved = moveMap(value)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_float(self) -> None:
    """Tests that MoveMap correctly moves floats"""
    for moveMap in self.maps:
      value = self.randFloat()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x = value + h
      y = value + v
      moved = moveMap(value)
      self.assertAlmostEqual(moved[0], x)
      self.assertAlmostEqual(moved[1], y)

  def test_region(self, ) -> None:
    """Tests that MoveMap correctly moves Region values. """
    for moveMap in self.maps:
      region = self.randRegion()
      h = moveMap.horizontalMove
      v = moveMap.verticalMove
      x0 = region.topLeft.x + h
      y0 = region.topLeft.y + v
      x1 = region.bottomRight.x + h
      y1 = region.bottomRight.y + v
      moved = moveMap(region)
      self.assertAlmostEqual(moved.topLeft.x, x0)
      self.assertAlmostEqual(moved.topLeft.y, y0)
      self.assertAlmostEqual(moved.bottomRight.x, x1)
      self.assertAlmostEqual(moved.bottomRight.y, y1)
