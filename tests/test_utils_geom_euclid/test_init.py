"""
TestInit provides the initial testing
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from icecream import ic
from worktoy.waitaminute.dispatch import DispatchException

from worktoy.work_test import BaseTest
from . import WesselPoint

if TYPE_CHECKING:  # pragma: no cover
  pass

ic.configureOutput(includeContext=True)


class TestInit(BaseTest):
  """
  TestInit provides the initial testing
  """

  def setUp(self) -> None:
    """Set up the test case."""
    super().setUp()
    self.samples = WesselPoint.samples(69, .1337, 80085)
    self.randomInteger.height = 100
    self.randomInteger.width = 1
    self.randomInteger.minVal = -69
    self.randomInteger.maxVal = 420
    self.randomFloat.height = 100
    self.randomFloat.width = 1
    self.randomFloat.minVal = -69.0
    self.randomFloat.maxVal = 420.0

  def test_init_args(self) -> None:
    """Test initialization with arguments."""
    pointFloat = WesselPoint(3.0, 4.0)  # floats
    self.assertAlmostEqual(pointFloat.x, 3.0)
    self.assertAlmostEqual(pointFloat.y, 4.0)
    self.assertIsInstance(pointFloat.x, float)
    self.assertIsInstance(pointFloat.y, float)
    pointInt = WesselPoint(69, 420)  # integers
    self.assertAlmostEqual(pointInt.x, 69.0)
    self.assertAlmostEqual(pointInt.y, 420.0)
    self.assertIsInstance(pointInt.x, float)
    self.assertIsInstance(pointInt.y, float)
    pointComplex = WesselPoint(1337 + 8085j)
    self.assertAlmostEqual(pointComplex.x, 1337.0)
    self.assertAlmostEqual(pointComplex.y, 8085.0)
    self.assertIsInstance(pointComplex.x, float)
    self.assertIsInstance(pointComplex.y, float)
    pointOne = WesselPoint(8008135.)
    self.assertAlmostEqual(pointOne.x, 8008135.0)
    self.assertAlmostEqual(pointOne.y, 0.0)

  def test_init_kwargs(self, ) -> None:
    """Test initialization with keyword arguments."""
    pointFloat = WesselPoint(x=3.0, y=4.0)  # floats
    self.assertAlmostEqual(pointFloat.x, 3.0)
    self.assertAlmostEqual(pointFloat.y, 4.0)
    self.assertIsInstance(pointFloat.x, float)
    self.assertIsInstance(pointFloat.y, float)
    pointInt = WesselPoint(y=420, x=69)  # integers
    self.assertAlmostEqual(pointInt.x, 69.0)
    self.assertAlmostEqual(pointInt.y, 420.0)
    self.assertIsInstance(pointInt.x, float)
    self.assertIsInstance(pointInt.y, float)
    pointOne = WesselPoint(y=420)
    self.assertAlmostEqual(pointOne.x, 0.0)
    self.assertAlmostEqual(pointOne.y, 420.0)

  def test_init_mixed(self, ) -> None:
    """Test initialization with mixed arguments."""
    pointMixed = WesselPoint(3.0, y=4.0)  # floats
    self.assertAlmostEqual(pointMixed.x, 3.0)
    self.assertAlmostEqual(pointMixed.y, 4.0)
    self.assertIsInstance(pointMixed.x, float)
    self.assertIsInstance(pointMixed.y, float)

  def test_init_no_args(self, ) -> None:
    """Test initialization with no arguments."""
    pointDefault = WesselPoint()  # default
    self.assertAlmostEqual(pointDefault.x, 0.0)
    self.assertAlmostEqual(pointDefault.y, 0.0)
    self.assertIsInstance(pointDefault.x, float)
    self.assertIsInstance(pointDefault.y, float)

  def test_init_bad_args(self, ) -> None:
    """Testing initialization with bad arguments."""
    badArgsList = [
      (3.0, 4.0, 5.0),  # too many positional arguments
      lambda yourmom: 'fat',  # wrong type
      'never gonna give you up',  # wrong type
      type('LOL', (), dict()),  # wrong type
      ]
    for badArgs in badArgsList:
      with self.assertRaises(DispatchException) as context:
        if isinstance(badArgs, tuple):
          _ = WesselPoint(*badArgs)
        else:
          _ = WesselPoint(badArgs)
      e = context.exception
      self.assertIs(e.dispatch, WesselPoint.__init__)
      if isinstance(badArgs, tuple):
        self.assertEqual(e.args, badArgs)
      else:
        self.assertEqual(e.args, (badArgs,))

  def test_get_item_index(self, ) -> None:
    """Test getting items by index."""
    point = WesselPoint(3.0, 4.0)
    self.assertAlmostEqual(point[0], 3.0)
    self.assertAlmostEqual(point[1], 4.0)
    trollIndex = self.randomInteger
    for indices in trollIndex:
      index = indices[0]
      expected = point.y if index % 2 else point.x
      self.assertAlmostEqual(point[index % 2], expected)

  def test_get_item_key(self, ) -> None:
    """Test getting items by key."""
    point = WesselPoint(3.0, 4.0)
    for dim in WesselPoint.getDimensions():
      for key in dim.keyGroup:
        expected = dim.__get__(point, WesselPoint)
        actual = point[key]
        self.assertAlmostEqual(actual, expected)

  def test_get_item_slice(self, ) -> None:
    """Test getting items by slice."""
    point = WesselPoint(3.0, 4.0)
    sliceX = point[0:1]
    self.assertIsInstance(sliceX, tuple)
    self.assertEqual(len(sliceX), 1)
    self.assertAlmostEqual(sliceX[0], 3.0)
    sliceY = point[1:2]
    self.assertIsInstance(sliceY, tuple)
    self.assertEqual(len(sliceY), 1)
    self.assertAlmostEqual(sliceY[0], 4.0)
    sliceXY = point[0:2]
    self.assertIsInstance(sliceXY, tuple)
    self.assertEqual(len(sliceXY), 2)
    self.assertAlmostEqual(sliceXY[0], 3.0)
    self.assertAlmostEqual(sliceXY[1], 4.0)

  def test_get_item_bad_type(self, ) -> None:
    """Test getting items with a bad type."""
    point = WesselPoint(69, 420)
    badlyTypes = [0.80085, ]
    for bad in badlyTypes:
      with self.assertRaises(DispatchException) as context:
        _ = point[bad]
      e = context.exception
      self.assertIs(e.dispatch, WesselPoint.__getitem__)
      self.assertEqual(e.args, (bad,))

  def test_add_scalar(self, ) -> None:
    """Test adding a scalar to a WesselPoint."""
    for point in self.samples:
      for scalar in self.randomFloat.row:
        newPoint = point + scalar
        self.assertIsInstance(newPoint, WesselPoint)
        self.assertAlmostEqual(newPoint.x, point.x + scalar)
        self.assertAlmostEqual(newPoint.y, point.y + scalar)

  def test_sub_scalar(self, ) -> None:
    """Test subtracting a scalar from a WesselPoint."""
    for point in self.samples:
      for scalar in self.randomFloat.row:
        newPoint = point - scalar
        self.assertIsInstance(newPoint, WesselPoint)
        self.assertAlmostEqual(newPoint.x, point.x - scalar)
        self.assertAlmostEqual(newPoint.y, point.y - scalar)

  def test_mul_scalar(self, ) -> None:
    """Test multiplying a WesselPoint by a scalar."""
    for point in self.samples:
      for scalar in self.randomFloat.row:
        newPoint = point * scalar
        self.assertIsInstance(newPoint, WesselPoint)
        self.assertAlmostEqual(newPoint.x, point.x * scalar)
        self.assertAlmostEqual(newPoint.y, point.y * scalar)
        newPoint = point @ scalar
        self.assertIsInstance(newPoint, WesselPoint)
        self.assertAlmostEqual(newPoint.x, point.x * scalar)
        self.assertAlmostEqual(newPoint.y, point.y * scalar)
        newPoint = point / scalar
        self.assertIsInstance(newPoint, WesselPoint)
        self.assertAlmostEqual(newPoint.x, point.x / scalar)
        self.assertAlmostEqual(newPoint.y, point.y / scalar)
