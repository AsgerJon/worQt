"""TestPlaneMisc tests miscellaneous methods on the Plane class."""
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


class TestPlaneMisc(AbstractTest):
  """TestPlane tests the Plane class."""

  def test_iter(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    r0, r1 = plane
    self.assertAlmostEqual(r0, plane.r0)
    self.assertAlmostEqual(r1, plane.r1)

  def test_len(self) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    self.assertEqual(len(plane), 2)

  def test_abs(self) -> None:
    """Test the Plane class."""
    x, y = self.randFloats()
    r = x * x + y * y
    plane = Plane(x, y)
    self.assertAlmostEqual(abs(plane) ** 2, r)

  def test_bool(self) -> None:
    """Test the Plane class."""
    nullPlane = Plane()
    self.assertFalse(nullPlane)
    plane = Plane(*self.randFloats())
    self.assertTrue(plane)

  def test_complex(self, ) -> None:
    """Test the Plane class."""
    plane = Plane(*self.randFloats())
    complexPlane = complex(plane)
    self.assertAlmostEqual(complexPlane.real, plane.r0)
    self.assertAlmostEqual(complexPlane.imag, plane.r1)
