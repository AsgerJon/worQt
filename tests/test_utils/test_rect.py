"""
TestRect subclasses 'UtilsTest' and tests the 'worQt.utils.geom.Rect'
value type: its overloaded constructors, the derived geometry (size,
corners, center), the 'Q' conversion, and containment.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect, QRectF

from worQt.utils.geom import Rect, Point2D, Size

from . import UtilsTest


class TestRect(UtilsTest):
  """Tests for the 'Rect' value type."""

  def test_edge_constructor(self) -> None:
    """Four integers fix the left/top/right/bottom edges."""
    rect = Rect(10, 20, 110, 120)
    self.assertEqual(rect.left, 10)
    self.assertEqual(rect.top, 20)
    self.assertEqual(rect.right, 110)
    self.assertEqual(rect.bottom, 120)

  def test_empty_constructor(self) -> None:
    """The no-argument form is the degenerate rect at the origin."""
    rect = Rect()
    self.assertEqual(rect.left, 0)
    self.assertEqual(rect.right, 0)

  def test_corner_constructor(self) -> None:
    """Two points fix the top-left and bottom-right corners."""
    rect = Rect(Point2D(10, 20), Point2D(110, 120))
    self.assertEqual(rect.left, 10)
    self.assertEqual(rect.bottom, 120)

  def test_point_size_constructor(self) -> None:
    """A top-left point and a size place the rect."""
    rect = Rect(Point2D(10, 20), Size(100, 100))
    self.assertEqual(rect.left, 10)
    self.assertEqual(rect.right, 110)
    self.assertEqual(rect.bottom, 120)

  def test_size_constructor(self) -> None:
    """A bare size places the rect at the origin."""
    rect = Rect(Size(100, 80))
    self.assertEqual(rect.left, 0)
    self.assertEqual(rect.top, 0)
    self.assertEqual(rect.right, 100)
    self.assertEqual(rect.bottom, 80)

  def test_qrect_constructor(self) -> None:
    """A 'QRect' is accepted strictly (x/y/width/height to edges)."""
    rect = Rect(QRect(10, 20, 100, 100))
    self.assertEqual(rect.left, 10)
    self.assertEqual(rect.right, 110)
    self.assertEqual(rect.bottom, 120)

  def test_qrectf_constructor(self) -> None:
    """A 'QRectF' is accepted strictly and rounded."""
    rect = Rect(QRectF(10.0, 20.0, 100.0, 100.0))
    self.assertEqual(rect.left, 10)
    self.assertEqual(rect.right, 110)

  def test_copy_constructor(self) -> None:
    """A 'Rect' rebuilds an independent copy via 'THIS'."""
    original = Rect(10, 20, 110, 120)
    copy = Rect(original)
    self.assertEqual(copy.right, 110)
    copy.right = 999
    self.assertEqual(original.right, 110)

  def test_derived_geometry(self) -> None:
    """Width, height, size, and center derive from the edges."""
    rect = Rect(10, 20, 110, 120)
    self.assertEqual(rect.width, 100)
    self.assertEqual(rect.height, 100)
    self.assertEqual(rect.size.width, 100)
    self.assertEqual(rect.size.height, 100)
    self.assertEqual(rect.center.x, 60)
    self.assertEqual(rect.center.y, 70)

  def test_corners(self) -> None:
    """The four corner points read off the edges."""
    rect = Rect(10, 20, 110, 120)
    self.assertEqual(rect.topLeft.x, 10)
    self.assertEqual(rect.topLeft.y, 20)
    self.assertEqual(rect.bottomRight.x, 110)
    self.assertEqual(rect.bottomRight.y, 120)
    self.assertEqual(rect.topRight.x, 110)
    self.assertEqual(rect.topRight.y, 20)
    self.assertEqual(rect.bottomLeft.x, 10)
    self.assertEqual(rect.bottomLeft.y, 120)

  def test_qf_conversion(self) -> None:
    """The 'QF' field yields a matching 'QRectF'."""
    qRectF = Rect(10, 20, 110, 120).QF
    self.assertAlmostEqual(qRectF.x(), 10.0)
    self.assertAlmostEqual(qRectF.width(), 100.0)

  def test_q_conversion(self) -> None:
    """The 'Q' field yields a matching 'QRect'."""
    qRect = Rect(10, 20, 110, 120).Q
    self.assertIsInstance(qRect, QRect)
    self.assertEqual(qRect.x(), 10)
    self.assertEqual(qRect.y(), 20)
    self.assertEqual(qRect.width(), 100)
    self.assertEqual(qRect.height(), 100)

  def test_contains_point(self) -> None:
    """A point inside the edges is contained; one outside is not."""
    rect = Rect(0, 0, 100, 100)
    self.assertIn(Point2D(50, 50), rect)
    self.assertNotIn(Point2D(150, 50), rect)

  def test_contains_rect(self) -> None:
    """A rect fully within the edges is contained."""
    outer = Rect(0, 0, 100, 100)
    inner = Rect(10, 10, 90, 90)
    self.assertIn(inner, outer)
    self.assertNotIn(outer, inner)

  def test_str(self) -> None:
    """The string form reports all four edges."""
    self.assertEqual(str(Rect(10, 20, 110, 120)), 'Rect(10, 20, 110, 120)')
