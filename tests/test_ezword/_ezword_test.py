"""
EZWordTest and EZWordWidgetTest are the base classes for the tests of
'worQt.ezword'. 'EZWordTest' subclasses 'BaseTest' for the text model,
which needs no Qt. 'EZWordWidgetTest' subclasses 'WidgetTest' for the
GUI: it runs in a 'QuietEZWordApp', whose window answers the file
questions and whose exit guard answers the save question, so no modal
dialog ever opens, and it gives each test a fresh window and a
temporary directory to save in.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import tempfile
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from worktoy.desc import AttriBox
from worktoy.work_test import BaseTest

from worQt.ezword.gui import EZWordApp, EZWordWindow, PageWidget
from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_CANCEL = QMessageBox.StandardButton.Cancel
_NO_MOD = Qt.KeyboardModifier.NoModifier


class QuietEZWordWindow(EZWordWindow):
  """
  An 'EZWordWindow' whose file questions a test answers: 'openPath' and
  'savePath' stand in for the file dialogs, and an empty one cancels.
  """

  openPath = AttriBox[str]('')
  savePath = AttriBox[str]('')

  def askOpenPath(self) -> str:
    return self.openPath

  def askSavePath(self) -> str:
    return self.savePath


class QuietEZWordApp(EZWordApp):
  """
  An 'EZWordApp' whose window is a 'QuietEZWordWindow' and whose save
  question a test answers through 'answer', counting how often it was
  asked.
  """

  __window_class__ = QuietEZWordWindow

  answer = AttriBox[QMessageBox.StandardButton](_CANCEL)
  askCount = AttriBox[int](0)

  def askToSave(self) -> QMessageBox.StandardButton:
    self.askCount += 1
    return self.answer


class EZWordTest(BaseTest):
  """
  EZWordTest subclasses 'BaseTest' and is the base class for the tests of
  the EZWord text model.
  """


class EZWordWidgetTest(WidgetTest):
  """
  EZWordWidgetTest subclasses 'WidgetTest' and is the base class for the
  tests of the EZWord GUI.
  """

  __application_type__ = QuietEZWordApp

  def setUp(self) -> None:
    """Every test starts with the save question cancelled, a fresh
    window - the harness deletes the windows a test opens - and an empty
    temporary directory. Closing the window, as ':wq' does, must not
    quit the application the tests run in."""
    super().setUp()
    self.__temp_dir__ = tempfile.TemporaryDirectory()
    app = self.app
    app.setQuitOnLastWindowClosed(False)
    app.answer, app.askCount = _CANCEL, 0
    app.__main_window__ = None

  def tearDown(self) -> None:
    try:
      super().tearDown()
    finally:
      self.__temp_dir__.cleanup()

  def path(self, name: str) -> str:
    """The path of a file named 'name' in this test's directory."""
    return os.path.join(self.__temp_dir__.name, name)

  def insert(self, page: PageWidget, text: str) -> None:
    """Type 'text' on 'page' the Vi way: 'i', the text, then Esc."""
    self.typeText(page, 'i')
    self.typeText(page, text)
    self.key(page, Qt.Key.Key_Escape, _NO_MOD, '\x1b')

  def ex(self, page: PageWidget, command: str) -> None:
    """Run the ex command 'command' on 'page': ':', it, then Enter."""
    self.typeText(page, ':%s' % command)
    self.key(page, Qt.Key.Key_Return, _NO_MOD, '\r')

  def openWindow(self) -> QuietEZWordWindow:
    """The application's window, shown live, so its UI is built and its
    page painted."""
    window = self.app.window
    self.showLive(window)
    return window
