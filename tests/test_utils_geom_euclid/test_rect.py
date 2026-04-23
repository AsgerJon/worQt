"""
TestRect tests the Rect class in utils.geom.euclid.rect.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic

from tests.test_utils_geom_euclid import EuclidTest
from worQt.utils.geom import Rect, Point2D, Size, InSets

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestRect(EuclidTest):
  """
  TestRect tests the Rect class in utils.geom.euclid.rect.
  """

  def test_init_args(self) -> None:
    rect = Rect(0, 0, 10, 10)
    self.assertEqual(rect.left, 0)
    self.assertEqual(rect.top, 0)
    self.assertEqual(rect.right, 10)
    self.assertEqual(rect.bottom, 10)

  def test_init_kwargs(self) -> None:
    rect = Rect(left=0, top=0, right=10, bottom=10)
    self.assertEqual(rect.left, 0)
    self.assertEqual(rect.top, 0)
    self.assertEqual(rect.right, 10)
    self.assertEqual(rect.bottom, 10)

  def test_init_this(self, ) -> None:
    rect1 = Rect(0, 0, 10, 10)
    rect2 = Rect(rect1)
    self.assertEqual(rect2.left, rect1.left)
    self.assertEqual(rect2.top, rect1.top)
    self.assertEqual(rect2.right, rect1.right)
    self.assertEqual(rect2.bottom, rect1.bottom)

  def test_add_int(self, ) -> None:
    rect = Rect(0, 0, 10, 10) + 5
    self.assertEqual(rect.left, 5)
    self.assertEqual(rect.top, 5)
    self.assertEqual(rect.right, 15)
    self.assertEqual(rect.bottom, 15)

  def test_init_points(self, ) -> None:
    P, Q = Point2D(0, 0), Point2D(10, 10)
    rect = Rect(P, Q)
    self.assertEqual(rect.left, P.x)
    self.assertEqual(rect.top, P.y)
    self.assertEqual(rect.right, Q.x)
    self.assertEqual(rect.bottom, Q.y)

  def test_init_point_size(self, ) -> None:
    P = Point2D(0, 0)
    size = Size(69, 420)
    rect = Rect(P, size)
    self.assertEqual(rect.left, P.x)
    self.assertEqual(rect.top, P.y)
    self.assertEqual(rect.right, P.x + size.width)
    self.assertEqual(rect.bottom, P.y + size.height)

  def test_sub_int(self, ) -> None:
    """
    Testing integer subtraction. Please note that this overload is
    inherited from the 'EuclideanObject' parent class of 'Rect'.
    """
    for rect in self.randomRect.row:
      for loss in self.randomInteger.row:
        subRect = rect - loss
        self.assertEqual(subRect.left, rect.left - loss)
        self.assertEqual(subRect.top, rect.top - loss)
        self.assertEqual(subRect.right, rect.right - loss)
        self.assertEqual(subRect.bottom, rect.bottom - loss)

  def test_sub_point(self, ) -> None:
    """
    Testing 'Point2D' objects subtracted from 'Rect' objects. The expected
    result is that translation of the 'Rect' object in the negative
    direction of the given 'Point2D' object. In other words, positive
    translation in the direction of the negation of the given 'Point2D'
    object.
    """
    for rect in self.randomRect.row:
      for point in self.randomPoint2D.row:
        subRect = rect - point
        translatedRect = rect + (-point)
        self.assertEqual(subRect, translatedRect)
        expectedLeft = rect.left - point.x
        expectedTop = rect.top - point.y
        expectedRight = rect.right - point.x
        expectedBottom = rect.bottom - point.y
        self.assertEqual(subRect.left, expectedLeft)
        self.assertEqual(subRect.top, expectedTop)
        self.assertEqual(subRect.right, expectedRight)
        self.assertEqual(subRect.bottom, expectedBottom)

  def test_add_point(self, ) -> None:
    """
    Testing 'Point2D' objects added to 'Rect' objects. The expected result is
    that translation of the 'Rect' object in the direction of the given
    'Point2D' object.
    """
    for rect in self.randomRect.row:
      for point in self.randomPoint2D.row:
        addRect = rect + point
        translatedRect = rect - (-point)
        self.assertEqual(addRect, translatedRect)
        expectedLeft = rect.left + point.x
        expectedTop = rect.top + point.y
        expectedRight = rect.right + point.x
        expectedBottom = rect.bottom + point.y
        self.assertEqual(addRect.left, expectedLeft)
        self.assertEqual(addRect.top, expectedTop)
        self.assertEqual(addRect.right, expectedRight)
        self.assertEqual(addRect.bottom, expectedBottom)

  def test_sub_in_sets(self, ) -> None:
    """
    Testing 'InSets' objects subtracted from 'Rect' objects. The expected
    result is that the 'Rect' object is translated by the negative of the
    given 'InSets' object.
    """
    for rect in self.randomRect.row:
      for inSets in self.randomInSets.row:
        subRect = rect - inSets
        expectedWidth = rect.width - inSets.left - inSets.right
        expectedHeight = rect.height - inSets.top - inSets.bottom
        expectedLeft = rect.left + inSets.left
        expectedTop = rect.top + inSets.top
        expectedRight = rect.right - inSets.right
        expectedBottom = rect.bottom - inSets.bottom
        actualWidth = subRect.width
        actualHeight = subRect.height
        actualLeft = subRect.left
        actualTop = subRect.top
        actualRight = subRect.right
        actualBottom = subRect.bottom
        self.assertEqual(subRect.width, expectedWidth)
        self.assertEqual(subRect.height, expectedHeight)
        self.assertEqual(subRect.left, expectedLeft)
        self.assertEqual(subRect.top, expectedTop)
        self.assertEqual(subRect.right, expectedRight)
        self.assertEqual(subRect.bottom, expectedBottom)

  def test_add_in_sets(self, ) -> None:
    """
    Testing 'InSets' objects added to 'Rect' objects. The expected result is
    that the 'Rect' object is translated by the given 'InSets' object.
    """
    for rect in self.randomRect.row:
      for inSets in self.randomInSets.row:
        addRect = rect + inSets
        expectedWidth = rect.width + inSets.left + inSets.right
        expectedHeight = rect.height + inSets.top + inSets.bottom
        expectedLeft = rect.left - inSets.left
        expectedTop = rect.top - inSets.top
        expectedRight = rect.right + inSets.right
        expectedBottom = rect.bottom + inSets.bottom
        actualWidth = addRect.width
        actualHeight = addRect.height
        actualLeft = addRect.left
        actualTop = addRect.top
        actualRight = addRect.right
        actualBottom = addRect.bottom
        self.assertEqual(addRect.width, expectedWidth)
        self.assertEqual(addRect.height, expectedHeight)
        self.assertEqual(addRect.left, expectedLeft)
        self.assertEqual(addRect.top, expectedTop)
        self.assertEqual(addRect.right, expectedRight)
        self.assertEqual(addRect.bottom, expectedBottom)

  # def test_dev_null(self, ) -> None:
  #   rect = Rect(4, 4, 20, 20)
  #   inSets = InSets(2, 2, 2, 2, )
  #   ic(rect)
  #   ic(rect - inSets)
  #   ic(rect + inSets)
