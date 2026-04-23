"""
TestPoint2D tests the Point2D class from the utils.geom.euclid module. It
includes tests for initialization, string representation, equality,
and distance calculation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QPoint, QPointF
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import ExceptionInfo

from worQt.utils.geom import Point2D
from . import EuclidTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestPoint2D(EuclidTest):
  """
  TestPoint2D tests the Point2D class from the utils.geom.euclid module. It
  includes tests for initialization, string representation, equality,
  and distance calculation.
  """

  def test_init_int_int(self) -> None:
    """Test initialization of Point2D."""
    point = Point2D(69, 420)
    self.assertEqual(point.x, 69)
    self.assertEqual(point.y, 420)
    self.assertIsInstance(point.x, Point2D.x.valueType)
    self.assertIsInstance(point.y, Point2D.y.valueType)

  def test_init_float_float(self) -> None:
    """
    Test initialization of Point2D with floats. Please note that these
    floats must be integer in size, that is: 'float.is_integer' must
    return True for these floats.
    """
    point = Point2D(69.0, 420.0)
    self.assertEqual(point.x, 69)
    self.assertEqual(point.y, 420)
    self.assertIsInstance(point.x, Point2D.x.valueType)
    self.assertIsInstance(point.y, Point2D.y.valueType)

  def test_init_kwargs(self) -> None:
    """Test initialization of Point2D with keyword arguments."""
    point = Point2D(x=69, y=420)
    self.assertEqual(point.x, 69)
    self.assertEqual(point.y, 420)
    self.assertIsInstance(point.x, Point2D.x.valueType)
    self.assertIsInstance(point.y, Point2D.y.valueType)

  def test_init_this(self, ) -> None:
    """Test initialization of Point2D with 'this' argument."""
    point = Point2D(69, 420)
    pointThis = Point2D(point)
    self.assertEqual(pointThis.x, 69)
    self.assertEqual(pointThis.y, 420)
    self.assertIsInstance(pointThis.x, Point2D.x.valueType)
    self.assertIsInstance(pointThis.y, Point2D.y.valueType)

  def test_init_q(self) -> None:
    """Test initialization of Point2D with QPoint."""
    qPoint = QPoint(69, 420)
    point = Point2D(qPoint)
    self.assertEqual(point.x, 69)
    self.assertEqual(point.y, 420)
    self.assertIsInstance(point.x, Point2D.x.valueType)
    self.assertIsInstance(point.y, Point2D.y.valueType)

  def test_init_qf(self) -> None:
    """Test initialization of Point2D with QPointF."""
    qPointF = QPointF(69.0, 420.0)
    point = Point2D(qPointF)
    self.assertEqual(point.x, 69)
    self.assertEqual(point.y, 420)
    self.assertIsInstance(point.x, Point2D.x.valueType)
    self.assertIsInstance(point.y, Point2D.y.valueType)

  def test_dist_this(self) -> None:
    """Test distance calculation of Point2D."""
    point1 = Point2D(0, 0)
    point2 = Point2D(3, 4)
    self.assertEqual(point1.dist(point2), 5)
    self.assertEqual(point2.dist(point1), 5)

  def test_dist_q(self) -> None:
    """Test distance calculation of Point2D with QPoint."""
    point1 = Point2D(0, 0)
    qPoint = QPoint(3, 4)
    self.assertEqual(point1.dist(qPoint), 5)

  def test_dist_qf(self) -> None:
    """Test distance calculation of Point2D with QPointF."""
    point1 = Point2D(0, 0)
    qPointF = QPointF(3.0, 4.0)
    self.assertEqual(point1.dist(qPointF), 5)

  def test_dist_fallback(self) -> None:
    """Test distance calculation between Point2D and type implementing
    'dist' method."""

    class AltPoint:
      __slots__ = ('x', 'y')

      def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

      def dist(self, other: Any) -> float:
        dx = self.x - other.x
        dy = self.y - other.y
        return (dx ** 2 + dy ** 2) ** 0.5

    point = Point2D(0, 0)
    altPoint = AltPoint(3, 4)
    self.assertEqual(point.dist(altPoint), 5)
