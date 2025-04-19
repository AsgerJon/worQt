"""TestPlaneAdd tests the addition implementation on the Plane class."""
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


class TestPlaneAdd(AbstractTest):
  """TestPlaneAdd tests the addition implementation on the Plane class."""

  def test_add_plane_plane(self, ) -> None:
    """Test the Plane class."""
    plane1 = Plane(*self.randFloats())
    plane2 = Plane(*self.randFloats())
    plane3 = plane1 + plane2
    self.assertAlmostEqual(plane3.r0, plane1.r0 + plane2.r0)
    self.assertAlmostEqual(plane3.r1, plane1.r1 + plane2.r1)

  def test_add_plane_float(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    floatArg = self.randFloat()
    plane2 = plane + floatArg
    self.assertAlmostEqual(plane2.r0, plane.r0 + floatArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 + floatArg)

  def test_add_plane_int(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    intArg = self.randInt()
    plane2 = plane + intArg
    self.assertAlmostEqual(plane2.r0, plane.r0 + intArg)
    self.assertAlmostEqual(plane2.r1, plane.r1 + intArg)

  def test_add_plane_complex(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    complexArg = self.randComplex()
    plane2 = plane + complexArg
    self.assertAlmostEqual(plane2.r0, plane.r0 + complexArg.real)
    self.assertAlmostEqual(plane2.r1, plane.r1 + complexArg.imag)

  def test_iadd_int(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane += 69
    self.assertAlmostEqual(plane.r0, r0 + 69)
    self.assertAlmostEqual(plane.r1, r1 + 69)

  def test_iadd_float(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane += 0.420
    self.assertAlmostEqual(plane.r0, r0 + 0.420)
    self.assertAlmostEqual(plane.r1, r1 + 0.420)

  def test_iadd_complex(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane += 69 + 420j
    self.assertAlmostEqual(plane.r0, r0 + 69)
    self.assertAlmostEqual(plane.r1, r1 + 420)

  def test_iadd_tuple(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane += (69, 420)
    self.assertAlmostEqual(plane.r0, r0 + 69)
    self.assertAlmostEqual(plane.r1, r1 + 420)

  def test_iadd_list(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane += [69, 420]
    self.assertAlmostEqual(plane.r0, r0 + 69)
    self.assertAlmostEqual(plane.r1, r1 + 420)

  def test_iadd_plane(self, ) -> None:
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    plane2 = Plane(69, 420)
    plane += plane2
    self.assertAlmostEqual(plane.r0, r0 + plane2.r0)
    self.assertAlmostEqual(plane.r1, r1 + plane2.r1)

  def test_radd_float(self, ) -> None:
    plane = Plane(*self.randFloats())
    plane2 = 420.69 + plane
    self.assertAlmostEqual(plane2.r0, 420.69 + plane.r0)
    self.assertAlmostEqual(plane2.r1, 420.69 + plane.r1)

  def test_radd_int(self, ) -> None:
    plane = Plane(*self.randFloats())
    plane2 = 420 + plane
    self.assertAlmostEqual(plane2.r0, 420 + plane.r0)
    self.assertAlmostEqual(plane2.r1, 420 + plane.r1)

  def test_radd_complex(self, ) -> None:
    plane = Plane(*self.randFloats())
    plane2 = 69 + 420j + plane
    self.assertAlmostEqual(plane2.r0, 69 + plane.r0)
    self.assertAlmostEqual(plane2.r1, 420 + plane.r1)

  def test_radd_tuple(self, ) -> None:
    plane = Plane(*self.randFloats())
    plane2 = (69, 420) + plane
    self.assertAlmostEqual(plane2.r0, 69 + plane.r0)
    self.assertAlmostEqual(plane2.r1, 420 + plane.r1)

  def test_radd_list(self, ) -> None:
    plane = Plane(*self.randFloats())
    plane2 = [69, 420] + plane
    self.assertAlmostEqual(plane2.r0, 69 + plane.r0)
    self.assertAlmostEqual(plane2.r1, 420 + plane.r1)
