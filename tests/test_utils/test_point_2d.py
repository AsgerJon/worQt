"""
TestPoint2D subclasses 'UtilsTest' and tests the 'worQt.utils.geom.Point2D'
value type: its overloaded constructors, the 'Q'/'QF' conversions, and the
'Point' alias.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF

from worQt.utils.geom import Point2D, Point

from . import UtilsTest


class TestPoint2D(UtilsTest):
  """Tests for the 'Point2D' value type."""

  def test_int_constructor(self) -> None:
    """Two integers fix 'x' and 'y' directly."""
    point = Point2D(3, 4)
    self.assertEqual(point.x, 3)
    self.assertEqual(point.y, 4)

  def test_empty_constructor(self) -> None:
    """The no-argument form defaults to the origin."""
    point = Point2D()
    self.assertEqual(point.x, 0)
    self.assertEqual(point.y, 0)

  def test_float_constructor(self) -> None:
    """Two floats are rounded to integer components."""
    point = Point2D(3.4, 4.6)
    self.assertEqual(point.x, 3)
    self.assertEqual(point.y, 5)

  def test_qpoint_constructor(self) -> None:
    """A 'QPoint' is accepted strictly, copying its coordinates."""
    point = Point2D(QPoint(7, 8))
    self.assertEqual(point.x, 7)
    self.assertEqual(point.y, 8)

  def test_qpointf_constructor(self) -> None:
    """A 'QPointF' is accepted strictly and rounded."""
    point = Point2D(QPointF(7.6, 8.2))
    self.assertEqual(point.x, 8)
    self.assertEqual(point.y, 8)

  def test_copy_constructor(self) -> None:
    """A 'Point2D' rebuilds an independent copy via 'THIS'."""
    original = Point2D(5, 6)
    copy = Point2D(original)
    self.assertEqual(copy.x, original.x)
    self.assertEqual(copy.y, original.y)
    copy.x = 99
    self.assertEqual(original.x, 5)

  def test_q_conversion(self) -> None:
    """The 'Q' field yields a matching 'QPoint'."""
    point = Point2D(3, 4)
    qPoint = point.Q
    self.assertIsInstance(qPoint, QPoint)
    self.assertEqual(qPoint.x(), 3)
    self.assertEqual(qPoint.y(), 4)

  def test_qf_conversion(self) -> None:
    """The 'QF' field yields a matching 'QPointF'."""
    point = Point2D(3, 4)
    qPointF = point.QF
    self.assertIsInstance(qPointF, QPointF)
    self.assertAlmostEqual(qPointF.x(), 3.0)
    self.assertAlmostEqual(qPointF.y(), 4.0)

  def test_point_alias(self) -> None:
    """'Point' is an alias of 'Point2D'."""
    self.assertIs(Point, Point2D)

  def test_str(self) -> None:
    """The string form reports both components."""
    self.assertEqual(str(Point2D(3, 4)), 'Point2D(3, 4)')
