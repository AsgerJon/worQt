"""TestPlane tests the Plane class. """
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


class TestPlaneInit(AbstractTest):
  """TestPlane tests the Plane class."""

  def test_init_int_int(self, ) -> None:
    """Test the Plane class."""
    intIntArgs = self.randInts()
    intIntPlane = Plane(*intIntArgs)
    tuplePlane = Plane(intIntArgs)
    listPlane = Plane([*intIntArgs, ])
    self.assertAlmostEqual(intIntPlane.r0, intIntArgs[0])
    self.assertAlmostEqual(intIntPlane.r1, intIntArgs[1])
    self.assertAlmostEqual(tuplePlane.r0, intIntArgs[0])
    self.assertAlmostEqual(tuplePlane.r1, intIntArgs[1])
    self.assertAlmostEqual(listPlane.r0, intIntArgs[0])
    self.assertAlmostEqual(listPlane.r1, intIntArgs[1])

  def test_init_int_float(self, ) -> None:
    intFloatArgs = self.randIntFloat()
    intFloatPlane = Plane(*intFloatArgs)
    tuplePlane = Plane(intFloatArgs)
    listPlane = Plane([*intFloatArgs, ])
    self.assertAlmostEqual(intFloatPlane.r0, intFloatArgs[0])
    self.assertAlmostEqual(intFloatPlane.r1, intFloatArgs[1])
    self.assertAlmostEqual(tuplePlane.r0, intFloatArgs[0])
    self.assertAlmostEqual(tuplePlane.r1, intFloatArgs[1])
    self.assertAlmostEqual(listPlane.r0, intFloatArgs[0])
    self.assertAlmostEqual(listPlane.r1, intFloatArgs[1])

  def test_init_float_int(self, ) -> None:
    floatIntArgs = self.randFloatInt()
    floatIntPlane = Plane(*floatIntArgs, )
    tuplePlane = Plane(floatIntArgs)
    listPlane = Plane([*floatIntArgs, ])
    self.assertAlmostEqual(floatIntPlane.r0, floatIntArgs[0])
    self.assertAlmostEqual(floatIntPlane.r1, floatIntArgs[1])
    self.assertAlmostEqual(tuplePlane.r0, floatIntArgs[0])
    self.assertAlmostEqual(tuplePlane.r1, floatIntArgs[1])
    self.assertAlmostEqual(listPlane.r0, floatIntArgs[0])
    self.assertAlmostEqual(listPlane.r1, floatIntArgs[1])

  def test_init_float_float(self, ) -> None:
    floatFloatArgs = self.randFloats()
    floatFloatPlane = Plane(*floatFloatArgs)
    tuplePlane = Plane(floatFloatArgs)
    listPlane = Plane([*floatFloatArgs, ])
    self.assertAlmostEqual(floatFloatPlane.r0, floatFloatArgs[0])
    self.assertAlmostEqual(floatFloatPlane.r1, floatFloatArgs[1])
    self.assertAlmostEqual(tuplePlane.r0, floatFloatArgs[0])
    self.assertAlmostEqual(tuplePlane.r1, floatFloatArgs[1])
    self.assertAlmostEqual(listPlane.r0, floatFloatArgs[0])
    self.assertAlmostEqual(listPlane.r1, floatFloatArgs[1])

  def test_init_complex(self, ) -> None:
    complexArg = self.randComplex()
    complexPlane = Plane(complexArg)
    self.assertAlmostEqual(complexPlane.r0, complexArg.real)
    self.assertAlmostEqual(complexPlane.r1, complexArg.imag)

  def test_init_plane(self, ) -> None:
    r0, r1 = self.randFloats()
    plane = Plane(r0, r1)
    self.assertAlmostEqual(plane.r0, r0)
    self.assertAlmostEqual(plane.r1, r1)
    planePlane = Plane(plane)
    self.assertAlmostEqual(planePlane.r0, plane.r0)
    self.assertAlmostEqual(planePlane.r1, plane.r1)

  def test_init_plane_plane(self, ) -> None:
    r0, r1 = self.randFloats()
    plane = Plane(r0, r1)
    self.assertAlmostEqual(plane.r0, r0)
    self.assertAlmostEqual(plane.r1, r1)
    r2, r3 = self.randFloats()
    plane2 = Plane(r2, r3)
    self.assertAlmostEqual(plane2.r0, r2)
    self.assertAlmostEqual(plane2.r1, r3)
    planePlane = Plane(plane, plane2)
    tuplePlane = Plane((plane, plane2))
    listPlane = Plane([plane, plane2])
    self.assertAlmostEqual(planePlane.r0, plane2.r0 - plane.r0)
    self.assertAlmostEqual(planePlane.r1, plane2.r1 - plane.r1)
    self.assertAlmostEqual(tuplePlane.r0, plane2.r0 - plane.r0)
    self.assertAlmostEqual(tuplePlane.r1, plane2.r1 - plane.r1)
    self.assertAlmostEqual(listPlane.r0, plane2.r0 - plane.r0)
    self.assertAlmostEqual(listPlane.r1, plane2.r1 - plane.r1)
