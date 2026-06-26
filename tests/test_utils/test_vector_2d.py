"""
TestVector2D subclasses 'UtilsTest' and tests the
'worQt.utils.geom.Vector2D' value type: its overloaded constructors, the
magnitude fields, and the dot product.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QVector2D

from worQt.utils.geom import Vector2D, Point2D

from . import UtilsTest


class TestVector2D(UtilsTest):
  """Tests for the 'Vector2D' value type."""

  def test_int_constructor(self) -> None:
    """Two integers fix the components directly."""
    vector = Vector2D(3, 4)
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 4)

  def test_empty_constructor(self) -> None:
    """The no-argument form is the zero vector."""
    vector = Vector2D()
    self.assertEqual(vector.x, 0)
    self.assertEqual(vector.y, 0)

  def test_single_point_constructor(self) -> None:
    """A single point is the displacement from the origin."""
    vector = Vector2D(Point2D(3, 4))
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 4)

  def test_two_point_constructor(self) -> None:
    """Two points give the displacement from the first to the second."""
    vector = Vector2D(Point2D(1, 1), Point2D(4, 5))
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 4)

  def test_float_constructor(self) -> None:
    """Two floats are rounded to integer components."""
    vector = Vector2D(3.4, 4.6)
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 5)

  def test_copy_constructor(self) -> None:
    """A 'Vector2D' rebuilds an independent copy via 'THIS'."""
    vector = Vector2D(Vector2D(3, 4))
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 4)

  def test_qvector_constructor(self) -> None:
    """A 'QVector2D' is accepted strictly and rounded."""
    vector = Vector2D(QVector2D(3.4, 4.6))
    self.assertEqual(vector.x, 3)
    self.assertEqual(vector.y, 5)

  def test_magnitude(self) -> None:
    """A 3-4-5 triangle has magnitude 5 and squared magnitude 25."""
    vector = Vector2D(3, 4)
    self.assertEqual(vector.magSqr, 25)
    self.assertAlmostEqual(vector.mag, 5.0)

  def test_dot_product(self) -> None:
    """'__mul__' of two vectors is their dot product."""
    self.assertEqual(Vector2D(3, 4) * Vector2D(2, 1), 10)

  def test_str(self) -> None:
    """The string form reports both components."""
    self.assertEqual(str(Vector2D(3, 4)), 'Vector2D(3, 4)')
