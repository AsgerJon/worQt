"""TestRotatePointMap rotates objects about a given point by a given
angle. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import cos, sin, pi

from .. import AbstractTest
from worQt.tools.geometry import RotatePointMap as Map, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class TestRotatePoint(AbstractTest):
  """TestRotatePointMap tests the RotatePointMap class."""

  def setUp(self) -> None:
    """Set up the test case."""
    pointFloatMaps = [Map(*self.randPointFloat()) for _ in range(100)]
    float3Maps = [Map(*self.rand3Float()) for _ in range(100)]
    pointVectorMaps = [Map(*self.randPointVector()) for _ in range(100)]
    self.maps = [
        *pointFloatMaps,
        *float3Maps,
        *pointVectorMaps,
    ]

  def test_point(self, ) -> None:
    """Test that RotatePointMap correctly rotates points. """
    for rotateMap in self.maps:
      point = self.randPoint()
      angle = rotateMap.angle
      center = rotateMap.center
      vector = Vector(point, center)
