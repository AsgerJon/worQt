"""TestPlaneDiv tests the division implementation on the Plane class."""
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


class TestPlaneDiv(AbstractTest):
  """TestPlane tests the Plane class."""

  def test_truediv_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = 420.
    plane2 = plane / floatArg
    self.assertAlmostEqual(plane2.r0, plane.r0 / floatArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 / floatArg)

  def test_truediv_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = 69
    plane2 = plane / intArg
    self.assertAlmostEqual(plane2.r0, plane.r0 / intArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 / intArg)

  def test_itruediv_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    floatArg = 420.
    plane /= floatArg
    self.assertAlmostEqual(plane.r0, r0 / floatArg)
    self.assertAlmostEqual(plane.r1, r1 / floatArg)

  def test_itruediv_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    intArg = 69
    plane /= intArg
    self.assertAlmostEqual(plane.r0, r0 / intArg)
    self.assertAlmostEqual(plane.r1, r1 / intArg)

  def test_rtruediv_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = 420.
    plane2 = floatArg / plane
    self.assertAlmostEqual(plane2.r0, floatArg / plane.r0)
    self.assertAlmostEqual(plane2.r1, floatArg / plane.r1)

  def test_rtruediv_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = 69
    plane2 = intArg / plane
    self.assertAlmostEqual(plane2.r0, intArg / plane.r0)
    self.assertAlmostEqual(plane2.r1, intArg / plane.r1)

  def test_mod_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = 420.
    plane2 = plane % floatArg
    self.assertAlmostEqual(plane2.r0, plane.r0 % floatArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 % floatArg)

  def test_mod_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = 69
    plane2 = plane % intArg
    self.assertAlmostEqual(plane2.r0, plane.r0 % intArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 % intArg)

  def test_imod_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    floatArg = 420.
    plane %= floatArg
    self.assertAlmostEqual(plane.r0, r0 % floatArg)
    self.assertAlmostEqual(plane.r1, r1 % floatArg)

  def test_imod_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    intArg = 69
    plane %= intArg
    self.assertAlmostEqual(plane.r0, r0 % intArg)
    self.assertAlmostEqual(plane.r1, r1 % intArg)

  def test_rmod_float(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = 420.
    plane2 = floatArg % plane
    self.assertAlmostEqual(plane2.r0, floatArg % plane.r0)
    self.assertAlmostEqual(plane2.r1, floatArg % plane.r1)

  def test_rmod_int(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = 69
    plane2 = intArg % plane
    self.assertAlmostEqual(plane2.r0, intArg % plane.r0)
    self.assertAlmostEqual(plane2.r1, intArg % plane.r1)
