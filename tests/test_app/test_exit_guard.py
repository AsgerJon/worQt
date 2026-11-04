"""
TestExitGuard covers the unsaved-changes guard of 'App': 'confirmExit' with
each answer to the save question, the main window's 'closeEvent' honouring
it, the defaults of the 'hasUnsavedChanges'/'saveChanges' hooks, and the
' *' marker in the window title. The app answers 'askToSave' itself, so no
modal dialog ever opens.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QMessageBox
from worktoy.desc import AttriBox

from worQt.app import App
from worQt.qtest import AppTest
from worQt.windows import AbstractWindow

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

_SAVE = QMessageBox.StandardButton.Save
_DISCARD = QMessageBox.StandardButton.Discard
_CANCEL = QMessageBox.StandardButton.Cancel


class _GuardWin(AbstractWindow):
  """A minimal main window for the guarded app."""


class _GuardApp(App):
  """
  An 'App' whose unsaved state, answer to the save question and save
  result each test sets, and which counts how often it asked and saved.
  """

  __window_class__ = _GuardWin

  dirty = AttriBox[bool](False)
  answer = AttriBox[QMessageBox.StandardButton](_CANCEL)
  saveResult = AttriBox[bool](True)
  askCount = AttriBox[int](0)
  saveCount = AttriBox[int](0)

  def hasUnsavedChanges(self) -> bool:
    return self.dirty

  def saveChanges(self) -> bool:
    self.saveCount += 1
    return self.saveResult

  def askToSave(self) -> QMessageBox.StandardButton:
    self.askCount += 1
    return self.answer


class TestExitGuard(AppTest):
  """Tests for the unsaved-changes exit guard."""

  __application_type__ = _GuardApp

  def setUp(self) -> None:
    """Every test starts clean, with a fresh main window: the harness
    deletes the windows a test opens, so none survives into the next."""
    super().setUp()
    app = self.app
    app.dirty, app.answer, app.saveResult = False, _CANCEL, True
    app.askCount, app.saveCount = 0, 0
    app.__main_window__ = None

  def tearDown(self) -> None:
    self.app.__main_window__ = None  # the title watch must not find it
    super().tearDown()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONFIRM EXIT   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_clean_exit_asks_nothing(self) -> None:
    """With no unsaved changes the exit goes ahead without a question."""
    self.assertTrue(self.app.confirmExit())
    self.assertEqual(self.app.askCount, 0)

  def test_save_then_exit(self) -> None:
    """'Save' saves, and the exit goes ahead when the save succeeds."""
    self.app.dirty, self.app.answer = True, _SAVE
    self.assertTrue(self.app.confirmExit())
    self.assertEqual(self.app.saveCount, 1)

  def test_failed_save_stops_the_exit(self) -> None:
    """When saving fails - say the user cancels a file dialog - the exit
    is called off rather than losing the changes."""
    self.app.dirty, self.app.answer = True, _SAVE
    self.app.saveResult = False
    self.assertFalse(self.app.confirmExit())

  def test_discard_exits_without_saving(self) -> None:
    """'Discard' exits and saves nothing."""
    self.app.dirty, self.app.answer = True, _DISCARD
    self.assertTrue(self.app.confirmExit())
    self.assertEqual(self.app.saveCount, 0)

  def test_cancel_stops_the_exit(self) -> None:
    """'Cancel' calls the exit off and saves nothing."""
    self.app.dirty, self.app.answer = True, _CANCEL
    self.assertFalse(self.app.confirmExit())
    self.assertEqual(self.app.askCount, 1)
    self.assertEqual(self.app.saveCount, 0)

  def test_hook_defaults(self) -> None:
    """A plain 'App' has no unsaved changes and saves successfully."""
    self.assertFalse(App.hasUnsavedChanges(self.app))
    self.assertTrue(App.saveChanges(self.app))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CLOSE EVENT  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_close_allowed_when_clean(self) -> None:
    """Closing the window is accepted when there is nothing to lose."""
    event = QCloseEvent()
    self.app.window.closeEvent(event)
    self.assertTrue(event.isAccepted())

  def test_close_refused_on_cancel(self) -> None:
    """Closing the window is refused when the user cancels the exit."""
    self.app.dirty, self.app.answer = True, _CANCEL
    event = QCloseEvent()
    self.app.window.closeEvent(event)
    self.assertFalse(event.isAccepted())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TITLE MARKER   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_title_marks_unsaved_changes(self) -> None:
    """The title gains one ' *' while there are unsaved changes, however
    often it is refreshed, and loses it once they are gone."""
    window = self.app.window
    window.setWindowTitle('Document')
    self.app.dirty = True
    self.app._refreshTitle()
    self.app._refreshTitle()
    self.assertEqual(window.windowTitle(), 'Document *')
    self.app.dirty = False
    self.app._refreshTitle()
    self.assertEqual(window.windowTitle(), 'Document')

  def test_title_refresh_without_window(self) -> None:
    """Refreshing the title before any window exists does nothing."""
    self.app._refreshTitle()
    self.assertIsNone(self.app.__main_window__)

  def test_title_watch_starts_once(self) -> None:
    """Building the window starts the title watch, and starting it again
    keeps the one timer rather than adding another."""
    _ = self.app.window
    timer = self.app.__title_timer__
    self.assertTrue(timer.isActive())
    self.app._startTitleWatch()
    self.assertIs(self.app.__title_timer__, timer)
