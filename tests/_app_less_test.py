"""
AppLessTest subclasses 'BaseTest' from 'worQt.work_test' and provides the
basic test class for tests not requiring a running 'QApplication'.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.work_test import BaseTest

from . import Point2DSampler, SizeSampler, RectSampler, InSetsSampler

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  Point2DSamplerClass: TypeAlias = Type[Point2DSampler]
  SizeSamplerClass: TypeAlias = Type[SizeSampler]
  RectSamplerClass: TypeAlias = Type[RectSampler]


class AppLessTest(BaseTest):
  """
  AppLessTest subclasses 'BaseTest' from 'worQt.work_test' and provides the
  basic test class for tests not requiring a running 'QApplication'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  randomPoint2D = Point2DSampler()
  randomSize = SizeSampler()
  randomRect = RectSampler(0, 31, 256, 511)
  randomInSets = InSetsSampler()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setUp(self) -> None:
    """
    This method is called before each test method. It can be used to set up
    any state that is specific to each test.
    """
    super().setUp()
    self.randomPoint2D.rowCount = 8
    self.randomPoint2D.colCount = 8
    self.randomSize.rowCount = 8
    self.randomSize.colCount = 8
    self.randomRect.rowCount = 8
    self.randomRect.colCount = 8
    self.randomInteger.rowCount = 8
    self.randomInteger.colCount = 8
