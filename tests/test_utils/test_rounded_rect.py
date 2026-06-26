"""
TestRoundedRect subclasses 'UtilsTest' and tests the
'worQt.utils.geom.RoundedRect' value type: the inherited 'Rect'
constructors, the added rect-plus-radii constructor, and the 'hr'/'vr'
aliases.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.utils.geom import RoundedRect, Rect

from . import UtilsTest


class TestRoundedRect(UtilsTest):
  """Tests for the 'RoundedRect' value type."""

  def test_is_rect_subclass(self) -> None:
    """'RoundedRect' is a 'Rect'."""
    self.assertTrue(issubclass(RoundedRect, Rect))

  def test_rect_radii_constructor(self) -> None:
    """A rect plus two radii fixes the edges and the corner radii."""
    rounded = RoundedRect(Rect(10, 20, 110, 120), 8, 4)
    self.assertEqual(rounded.left, 10)
    self.assertEqual(rounded.top, 20)
    self.assertEqual(rounded.right, 110)
    self.assertEqual(rounded.bottom, 120)
    self.assertEqual(rounded.horizontalRadius, 8)
    self.assertEqual(rounded.verticalRadius, 4)

  def test_inherited_edge_constructor(self) -> None:
    """The inherited four-edge constructor leaves the radii at zero."""
    rounded = RoundedRect(10, 20, 110, 120)
    self.assertEqual(rounded.right, 110)
    self.assertEqual(rounded.horizontalRadius, 0)
    self.assertEqual(rounded.verticalRadius, 0)

  def test_radius_aliases(self) -> None:
    """'hr' and 'vr' alias the horizontal and vertical radii."""
    rounded = RoundedRect(Rect(0, 0, 10, 10), 8, 4)
    self.assertEqual(rounded.hr, 8)
    self.assertEqual(rounded.vr, 4)

  def test_derived_geometry_still_works(self) -> None:
    """Inherited derived geometry is unaffected by the radii."""
    rounded = RoundedRect(Rect(10, 20, 110, 120), 8, 4)
    self.assertEqual(rounded.width, 100)
    self.assertEqual(rounded.height, 100)
