"""
TestInSets subclasses 'UtilsTest' and tests the 'worQt.utils.geom.InSets'
value type: its overloaded constructors and the box-model arithmetic with
'Rect' and 'Size'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QMargins

from worQt.utils.geom import InSets, Rect, Size

from . import UtilsTest


class TestInSets(UtilsTest):
  """Tests for the 'InSets' value type."""

  def test_edge_constructor(self) -> None:
    """Four integers fix the left/top/right/bottom insets."""
    insets = InSets(1, 2, 3, 4)
    self.assertEqual(insets.left, 1)
    self.assertEqual(insets.top, 2)
    self.assertEqual(insets.right, 3)
    self.assertEqual(insets.bottom, 4)

  def test_horizontal_vertical_constructor(self) -> None:
    """Two integers fix the horizontal and vertical insets."""
    insets = InSets(5, 7)
    self.assertEqual(insets.left, 5)
    self.assertEqual(insets.right, 5)
    self.assertEqual(insets.top, 7)
    self.assertEqual(insets.bottom, 7)

  def test_uniform_constructor(self) -> None:
    """A single integer fixes every inset."""
    insets = InSets(3)
    self.assertEqual(insets.left, 3)
    self.assertEqual(insets.top, 3)
    self.assertEqual(insets.right, 3)
    self.assertEqual(insets.bottom, 3)

  def test_empty_constructor(self) -> None:
    """The no-argument form is the zero inset."""
    insets = InSets()
    self.assertEqual(insets.left, 0)
    self.assertEqual(insets.bottom, 0)

  def test_inner_outer_rect_constructor(self) -> None:
    """Two rects give the insets between an inner and outer rect."""
    insets = InSets(Rect(10, 10, 90, 90), Rect(0, 0, 100, 100))
    self.assertEqual(insets.left, 10)
    self.assertEqual(insets.top, 10)
    self.assertEqual(insets.right, 10)
    self.assertEqual(insets.bottom, 10)

  def test_inner_outer_size_constructor(self) -> None:
    """Two sizes give the centering insets between inner and outer."""
    insets = InSets(Size(80, 80), Size(100, 100))
    self.assertEqual(insets.left, 10)
    self.assertEqual(insets.right, 10)
    self.assertEqual(insets.top, 10)
    self.assertEqual(insets.bottom, 10)

  def test_insets_sub(self) -> None:
    """Two 'InSets' subtract edge by edge."""
    diff = InSets(10, 20, 30, 40) - InSets(1, 2, 3, 4)
    self.assertEqual(diff.left, 9)
    self.assertEqual(diff.bottom, 36)

  def test_rect_add_grows_outward(self) -> None:
    """'rect + insets' grows the rect outward by the insets."""
    grown = Rect(10, 10, 90, 90) + InSets(5, 5, 5, 5)
    self.assertEqual(grown.left, 5)
    self.assertEqual(grown.top, 5)
    self.assertEqual(grown.right, 95)
    self.assertEqual(grown.bottom, 95)

  def test_rect_sub_shrinks_inward(self) -> None:
    """'rect - insets' shrinks the rect inward by the insets."""
    shrunk = Rect(0, 0, 100, 100) - InSets(5, 5, 5, 5)
    self.assertEqual(shrunk.left, 5)
    self.assertEqual(shrunk.top, 5)
    self.assertEqual(shrunk.right, 95)
    self.assertEqual(shrunk.bottom, 95)

  def test_size_add_grows(self) -> None:
    """'size + insets' expands the size by the insets on each axis."""
    grown = Size(10, 10) + InSets(2, 2, 2, 2)
    self.assertEqual(grown.width, 14)
    self.assertEqual(grown.height, 14)

  def test_size_sub_shrinks(self) -> None:
    """'size - insets' contracts the size by the insets on each axis."""
    shrunk = Size(14, 14) - InSets(2, 2, 2, 2)
    self.assertEqual(shrunk.width, 10)
    self.assertEqual(shrunk.height, 10)

  def test_insets_add(self) -> None:
    """Two 'InSets' add edge by edge."""
    total = InSets(1, 2, 3, 4) + InSets(10, 20, 30, 40)
    self.assertEqual(total.left, 11)
    self.assertEqual(total.bottom, 44)

  def test_q_conversion(self) -> None:
    """The 'Q' field yields a matching 'QMargins'."""
    qMargins = InSets(1, 2, 3, 4).Q
    self.assertIsInstance(qMargins, QMargins)
    self.assertEqual(qMargins.left(), 1)
    self.assertEqual(qMargins.bottom(), 4)

  def test_str(self) -> None:
    """The string form reports all four insets."""
    self.assertEqual(str(InSets(1, 2, 3, 4)), 'InSets(1, 2, 3, 4)')
