"""TestRotateMap tests the RotateMap class."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from math import cos, sin, pi

from test_worqt_tools_geometry import AbstractTest
from worQt.tools.geometry import RotateMap

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class TestMove(AbstractTest):
  """TestMoveMap tests the ScaleMap class."""

  def setUp(self) -> None:
    """Set up the test case."""
    floatMaps = [RotateMap(self.randFloat()) for _ in range(100)]
    self.maps = [*floatMaps, ]

  def test_move_point(self) -> None:
    """Test the MoveMap class."""
    for moveMap in self.maps:
      point = self.randPoint()
      angle = moveMap.angle
      x = point.x * cos(angle) - point.y * sin(angle)
      y = point.x * sin(angle) + point.y * cos(angle)
      movedMap = moveMap(point)
      self.assertAlmostEqual(movedMap.x, x)
      self.assertAlmostEqual(movedMap.y, y)

  def test_move_vector(self, ) -> None:
    """Test that RotateMap correctly moves vector-valued points. """
    for moveMap in self.maps:
      point = self.randVector()
      angle = moveMap.angle
      x = point.x * cos(angle) - point.y * sin(angle)
      y = point.x * sin(angle) + point.y * cos(angle)
      movedMap = moveMap(point)
      self.assertAlmostEqual(movedMap.x, x)
      self.assertAlmostEqual(movedMap.y, y)

  def test_move_complex(self) -> None:
    """Test that RotateMap correctly moves complex-valued points. """
    for moveMap in self.maps:
      point = self.randComplex()
      angle = moveMap.angle
      x = point.real * cos(angle) - point.imag * sin(angle)
      y = point.real * sin(angle) + point.imag * cos(angle)
      movedMap = moveMap(point)
      self.assertAlmostEqual(movedMap.real, x)
      self.assertAlmostEqual(movedMap.imag, y)

  def test_move_floats(self) -> None:
    """Test that RotateMap correctly moves float-valued points. """
    for moveMap in self.maps:
      point = self.randFloats()
      angle = moveMap.angle
      x = point[0] * cos(angle) - point[1] * sin(angle)
      y = point[0] * sin(angle) + point[1] * cos(angle)
      movedMap = moveMap(point)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)

  def test_move_ints(self) -> None:
    """Test that RotateMap correctly moves integer-valued points. """
    for moveMap in self.maps:
      point = self.randInts()
      angle = moveMap.angle
      x = point[0] * cos(angle) - point[1] * sin(angle)
      y = point[0] * sin(angle) + point[1] * cos(angle)
      movedMap = moveMap(point)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)

  def test_move_float_float(self, ) -> None:
    """Test that RotateMap correctly moves floats."""
    for moveMap in self.maps:
      value = self.randFloat()
      angle = moveMap.angle
      x = value * cos(angle) - value * sin(angle)
      y = value * sin(angle) + value * cos(angle)
      movedMap = moveMap(value)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)

  def test_move_int_int(self, ) -> None:
    """Test that RotateMap correctly moves ints."""
    for moveMap in self.maps:
      value = self.randInt()
      x0, y0 = float(value), float(value)
      angle = moveMap.angle
      x = x0 * cos(angle) - x0 * sin(angle)
      y = x0 * sin(angle) + y0 * cos(angle)
      movedMap = moveMap(value)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)

  def test_move_int_float(self) -> None:
    """Tests that RotateMap correctly moves mixed types. """
    for moveMap in self.maps:
      intVal = self.randInt()
      floatVal = self.randFloat() / 2 / pi * 127
      angle = moveMap.angle
      x = intVal * cos(angle) - floatVal * sin(angle)
      y = intVal * sin(angle) + floatVal * cos(angle)
      movedMap = moveMap(intVal, floatVal)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)

  def test_move_float_int(self) -> None:
    """Tests that RotateMap correctly moves mixed types. """
    for moveMap in self.maps:
      intVal = self.randInt()
      floatVal = self.randFloat() / 2 / pi * 127
      angle = moveMap.angle
      x = floatVal * cos(angle) - intVal * sin(angle)
      y = floatVal * sin(angle) + intVal * cos(angle)
      movedMap = moveMap(floatVal, intVal)
      self.assertAlmostEqual(movedMap[0], x)
      self.assertAlmostEqual(movedMap[1], y)
