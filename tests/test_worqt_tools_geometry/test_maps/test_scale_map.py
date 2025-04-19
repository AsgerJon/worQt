"""TestScaleMap tests the ScaleMap class."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import cos, sin, pi

from .. import AbstractTest
from worQt.tools.geometry import ScaleMap, Region, Point, Size, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class TestScale(AbstractTest):
  """TestScaleMap tests the ScaleMap class."""

  def setUp(self) -> None:
    """Set up the test case."""
    randFloat = [self.randFloat() for _ in range(100)]
    posFloat = [abs(x) for x in randFloat]
    floatMaps = [ScaleMap(value) for value in posFloat]

    randFloats = [self.randFloats() for _ in range(100)]
    posFloats = [(abs(x), abs(y)) for x, y in randFloats]
    floatsMaps = [ScaleMap(*value) for value in posFloats]

    randInt = [self.randInt() for _ in range(100)]
    posInt = [abs(x) for x in randInt]
    intMaps = [ScaleMap(value) for value in posInt]

    randInts = [self.randInts() for _ in range(100)]
    posInts = [(abs(x), abs(y)) for x, y in randInts]
    intsMaps = [ScaleMap(*value) for value in posInts]

    randIntFloat = [self.randIntFloat() for _ in range(100)]
    posIntFloat = [(abs(x), abs(y)) for x, y in randIntFloat]
    intFloatMaps = [ScaleMap(*value) for value in posIntFloat]

    randFloatInt = [self.randFloatInt() for _ in range(100)]
    posFloatInt = [(abs(x), abs(y)) for x, y in randFloatInt]
    floatIntMaps = [ScaleMap(*value) for value in posFloatInt]

    randComplex = [self.randComplex() for _ in range(100)]
    posComplex = [(abs(z.real) + abs(z.imag) * 1j) for z in randComplex]
    complexMaps = [ScaleMap(value) for value in posComplex]

    randPointArgs = [self.randFloats() for _ in range(100)]
    posPointArgs = [(abs(x), abs(y)) for x, y in randPointArgs]
    posPoint = [Point(x, y) for x, y in posPointArgs]
    pointMaps = [ScaleMap(point) for point in posPoint]

    randVectorArgs = [self.randFloats() for _ in range(100)]
    posVectorArgs = [(abs(x), abs(y)) for x, y in randVectorArgs]
    posVector = [Vector(x, y) for x, y in posVectorArgs]
    vectorMaps = [ScaleMap(vector) for vector in posVector]

    self.maps = [
        *floatMaps,
        *floatsMaps,
        *intMaps,
        *intsMaps,
        *intFloatMaps,
        *floatIntMaps,
        *complexMaps,
        *pointMaps,
        *vectorMaps,
    ]

  def test_int_int(self, ) -> None:
    """Testing that ScaleMap correctly scales integer values."""
    for scaleMap in self.maps:
      x0, y0 = self.randInts()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = x0 * h
      y = y0 * v
      scaled = scaleMap(x0, y0)
      self.assertAlmostEqual(scaled[0], x)
      self.assertAlmostEqual(scaled[1], y)

  def test_int_float(self, ) -> None:
    """Testing that ScaleMap correctly scales mixed type values."""
    for scaleMap in self.maps:
      x0, y0 = self.randIntFloat()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = x0 * h
      y = y0 * v
      scaled = scaleMap(x0, y0)
      self.assertAlmostEqual(scaled[0], x)
      self.assertAlmostEqual(scaled[1], y)

  def test_float_int(self, ) -> None:
    """Testing that ScaleMap correctly scales mixed type values."""
    for scaleMap in self.maps:
      x0, y0 = self.randFloatInt()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = x0 * h
      y = y0 * v
      scaled = scaleMap(x0, y0)
      self.assertAlmostEqual(scaled[0], x)
      self.assertAlmostEqual(scaled[1], y)

  def test_float_float(self, ) -> None:
    """Testing that ScaleMap correctly scales float values."""
    for scaleMap in self.maps:
      x0, y0 = self.randFloats()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = x0 * h
      y = y0 * v
      scaled = scaleMap(x0, y0)
      self.assertAlmostEqual(scaled[0], x)
      self.assertAlmostEqual(scaled[1], y)

  def test_point(self, ) -> None:
    """Testing that ScaleMap correctly scales Point values."""
    for scaleMap in self.maps:
      point = self.randPoint()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = point.x * h
      y = point.y * v
      scaled = scaleMap(point)
      self.assertAlmostEqual(scaled.x, x)
      self.assertAlmostEqual(scaled.y, y)

  def test_size(self, ) -> None:
    """Testing that ScaleMap correctly scales Size values."""
    for scaleMap in self.maps:
      size = self.randSize()
      h = scaleMap.horizontalScale
      v = scaleMap.verticalScale
      x = size.width * h
      y = size.height * v
      scaled = scaleMap(size)
      self.assertAlmostEqual(scaled.width, abs(x))
      self.assertAlmostEqual(scaled.height, abs(y))

  def test_region(self, ) -> None:
    """Testing that ScaleMap correctly scales Region values."""
    for scaleMap in self.maps:
      region = self.randRegion()
      x = region.topLeft.x
      y = region.topLeft.y
      w = scaleMap.horizontalScale * region.width
      h = scaleMap.verticalScale * region.height
      x2 = x + w
      y2 = y + h
      scaled = scaleMap(region, _verbose=False)
      self.assertAlmostEqual(scaled.topLeft.x, x)
      self.assertAlmostEqual(scaled.topLeft.y, y)
      self.assertAlmostEqual(scaled.bottomRight.x, x2)
      self.assertAlmostEqual(scaled.bottomRight.y, y2)
      self.assertAlmostEqual(scaled.size.width, abs(w))
      self.assertAlmostEqual(scaled.size.height, abs(h))
