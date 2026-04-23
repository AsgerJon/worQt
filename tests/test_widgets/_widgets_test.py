"""
WidgetsTest subclasses 'WorQtTest' from the 'tests' package.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMainWindow
from worktoy.work_test import BaseTest

from tests import WorQtTest
from worQt.app import App
from worQt.windows import MainWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  AppClass: TypeAlias = Type[App]


class WidgetsTest(WorQtTest):
  """
  WidgetsTest subclasses 'WorQtTest' from the 'tests' package.
  """

  @classmethod
  def getAppClass(cls, ) -> AppClass:
    return App

  def setUp(self, ) -> None:
    BaseTest.setUp(self)
    appCls = self.getAppClass()
    self.app = appCls(MainWindow, 'WidgetsTest')
    with self.app as app:
      QMainWindow.setWindowIcon(app.window, app.appIcon)
      app.window.update()
      app.window.show()
      app.window.setMinimumSize(640, 640)
