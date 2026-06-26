"""
TestAlignum subclasses 'UtilsTest' and tests the
'worQt.utils.qee_num.Alignum' enumeration: its decomposition into
horizontal and vertical components, the 'combine' constructor, and the
'apply' placement that the box model relies on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QRect

from worQt.utils.qee_num import Alignum, HAlignum, VAlignum
from worQt.utils.geom import Rect, Size

from . import UtilsTest


class TestAlignum(UtilsTest):
  """Tests for the 'Alignum' alignment enumeration."""

  def test_decompose_center(self) -> None:
    """'CENTER' decomposes into centered horizontal and vertical parts."""
    self.assertIs(Alignum.CENTER.horizontal, HAlignum.CENTER)
    self.assertIs(Alignum.CENTER.vertical, VAlignum.CENTER)

  def test_decompose_corner(self) -> None:
    """A corner alignment decomposes into its edge components."""
    self.assertIs(Alignum.TOP_LEFT.horizontal, HAlignum.LEFT)
    self.assertIs(Alignum.TOP_LEFT.vertical, VAlignum.TOP)
    self.assertIs(Alignum.BOTTOM_RIGHT.horizontal, HAlignum.RIGHT)
    self.assertIs(Alignum.BOTTOM_RIGHT.vertical, VAlignum.BOTTOM)

  def test_combine(self) -> None:
    """'combine' rebuilds the member from its component parts."""
    combined = Alignum.combine(VAlignum.TOP, HAlignum.LEFT)
    self.assertIs(combined, Alignum.TOP_LEFT)

  def test_combine_order_independent(self) -> None:
    """'combine' accepts the horizontal and vertical parts in any order."""
    combined = Alignum.combine(HAlignum.RIGHT, VAlignum.BOTTOM)
    self.assertIs(combined, Alignum.BOTTOM_RIGHT)

  def test_apply_top_left(self) -> None:
    """'TOP_LEFT' places the moving rect flush in the static corner."""
    placed = Alignum.TOP_LEFT.apply(Rect(0, 0, 100, 100), Size(20, 10))
    self.assertEqual(placed.left, 0)
    self.assertEqual(placed.top, 0)
    self.assertEqual(placed.right, 20)
    self.assertEqual(placed.bottom, 10)

  def test_apply_center(self) -> None:
    """'CENTER' centers the moving rect within the static rect."""
    placed = Alignum.CENTER.apply(Rect(0, 0, 100, 100), Size(20, 10))
    self.assertEqual(placed.left, 40)
    self.assertEqual(placed.top, 45)
    self.assertEqual(placed.right, 60)
    self.assertEqual(placed.bottom, 55)

  def test_apply_bottom_right(self) -> None:
    """'BOTTOM_RIGHT' places the moving rect flush in the far corner."""
    placed = Alignum.BOTTOM_RIGHT.apply(Rect(0, 0, 100, 100), Size(20, 10))
    self.assertEqual(placed.left, 80)
    self.assertEqual(placed.top, 90)
    self.assertEqual(placed.right, 100)
    self.assertEqual(placed.bottom, 100)

  def test_apply_accepts_qrect(self) -> None:
    """'apply' normalises a Qt 'QRect' static area like a worQt 'Rect'."""
    placed = Alignum.CENTER.apply(QRect(0, 0, 100, 100), Size(20, 10))
    self.assertEqual(placed.left, 40)
    self.assertEqual(placed.top, 45)

  def test_apply_preserves_size(self) -> None:
    """Placement keeps the moving rect's size regardless of alignment."""
    for alignum in Alignum:
      placed = alignum.apply(Rect(0, 0, 100, 100), Size(20, 10))
      self.assertEqual(placed.width, 20)
      self.assertEqual(placed.height, 10)
