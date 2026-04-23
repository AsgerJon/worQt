"""
WorQtTest subclasses 'BaseTest' from the 'worktoy.work_test' package. It
forms the common base test for the 'worQt' package, where a running
QApplication is required. Tests on features not requiring such should
instead subclass 'BaseTest' from the 'worktoy.work_test' package directly.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication, QMainWindow
from worktoy.work_test import BaseTest

from tests import Point2DSampler, SizeSampler, RectSampler

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Union, Optional, TypeAlias, Type

  AppClass: TypeAlias = Type[QApplication]
  WindowClass: TypeAlias = Type[QMainWindow]


class WorQtTest(BaseTest):
  """
  WorQtTest subclasses 'BaseTest' from the 'worktoy.work_test' package. It
  forms the common base test for the 'worQt' package, where a running
  QApplication is required. Tests on features not requiring such should
  instead subclass 'BaseTest' from the 'worktoy.work_test' package directly.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  point2DSampler = Point2DSampler()
  sizeSampler = SizeSampler()
  rectSampler = RectSampler()

  #  Virtual Variables

  @classmethod
  def getAppClass(cls, ) -> AppClass:
    """
    Subclasses may override this method to specify a specific QApplication
    subclass. This method must return the class, not an instance. By
    default, it returns the standard QApplication class.
    """
    return QApplication

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def setUp(self, ) -> None:
    super().setUp()

    self.app = self.getAppClass()([])

  def tearDown(self, ) -> None:
    self.app.quit()
    super().tearDown()
