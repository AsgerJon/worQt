"""
TestInsets tests the 'InSets' class in utils.geom.euclid.insets.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from tests.test_utils_geom_euclid import EuclidTest
from worQt.utils.geom import InSets, Rect, Point2D, Size

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestInsets(EuclidTest):
  """
  TestInsets tests the 'InSets' class in utils.geom.euclid.insets.
  """

  def test_init_args(self, ) -> None:
    insets = InSets(1, 2, 3, 4)
    self.assertEqual(insets.left, 1)
    self.assertEqual(insets.top, 2)
    self.assertEqual(insets.right, 3)
    self.assertEqual(insets.bottom, 4)

  def test_init_kwargs(self, ) -> None:
    insets = InSets(left=1, top=2, right=3, bottom=4)
    self.assertEqual(insets.left, 1)
    self.assertEqual(insets.top, 2)
    self.assertEqual(insets.right, 3)
    self.assertEqual(insets.bottom, 4)

  def test_init_this(self, ) -> None:
    insets1 = InSets(1, 2, 3, 4)
    insets2 = InSets(insets1)
    self.assertEqual(insets2.left, insets1.left)
    self.assertEqual(insets2.top, insets1.top)
    self.assertEqual(insets2.right, insets1.right)
    self.assertEqual(insets2.bottom, insets1.bottom)

  def test_init_rects(self) -> None:
    innerTopLeft = Point2D(6, 7)
    outerTopLeft = Point2D(0, 0)
    innerSize = Size(100, 100)
    outerSize = Size(120, 120)
    innerRect = Rect(innerTopLeft, innerSize)
    outerRect = Rect(outerTopLeft, outerSize)
    insetsRects = InSets(innerRect, outerRect)
    self.assertEqual(insetsRects.left, 6)
    self.assertEqual(insetsRects.top, 7)
    self.assertEqual(insetsRects.right, 14)
    self.assertEqual(insetsRects.bottom, 13)
