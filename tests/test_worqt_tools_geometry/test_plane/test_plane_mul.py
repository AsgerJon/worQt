"""TestPlaneMul tests the multiplication implementation on the Plane
class. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import cos, sin, pi

from test_worqt_tools_geometry import AbstractTest
from worQt.tools.geometry import RotateMap, Plane

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class TestPlaneMul(AbstractTest):
  """TestPlane tests the Plane class."""

  def test_mul_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = self.randFloat()
    plane2 = plane * floatArg
    self.assertAlmostEqual(plane2.r0, plane.r0 * floatArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 * floatArg)

  def test_mul_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = self.randInt()
    plane2 = plane * intArg
    self.assertAlmostEqual(plane2.r0, plane.r0 * intArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 * intArg)

  def test_imul_float(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    floatArg = self.randFloat()
    plane *= floatArg
    self.assertAlmostEqual(plane.r0, r0 * floatArg)
    self.assertAlmostEqual(plane.r1, r1 * floatArg)

  def test_imul_int(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    intArg = self.randInt()
    plane *= intArg
    self.assertAlmostEqual(plane.r0, r0 * intArg)
    self.assertAlmostEqual(plane.r1, r1 * intArg)

  def test_rmul_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = self.randFloat()
    plane2 = floatArg * plane
    self.assertAlmostEqual(plane2.r0, plane.r0 * floatArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 * floatArg)

  def test_rmul_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = self.randInt()
    plane2 = intArg * plane
    self.assertAlmostEqual(plane2.r0, plane.r0 * intArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 * intArg)
