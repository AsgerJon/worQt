"""
RunTextWindow subclasses 'WordsAppTest' and covers the 'words' editor
window. Showing the window runs the build-once 'show()' lifecycle that
'AbstractWindow' provides: 'initUi' constructs the central editor and the
File menu (whose actions come from the '_action' helper), and a second
'show()' does not rebuild. The thin File-menu handlers are exercised too.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMenu, QPlainTextEdit

from worQt.words import TextWindow

from . import WordsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunTextWindow(WordsAppTest):
  """Tests for the 'words' editor window lifecycle and menu."""

  def run_show_builds_ui(self) -> None:
    """Showing the window builds the title and central editor via
    'AbstractWindow.show' -> 'initUi'."""
    window = TextWindow()
    window.show()
    QTest.qWait(50)
    self.assertTrue(window.isVisible())
    self.assertEqual(window.windowTitle(), 'words')
    self.assertIsInstance(window.centralWidget(), QPlainTextEdit)
    window.close()

  def run_file_menu_actions(self) -> None:
    """'initUi' builds a File menu with the five expected actions, each
    created through the '_action' helper on 'AbstractWindow'."""
    window = TextWindow()
    window.show()
    QTest.qWait(50)
    fileMenu = window.menuBar().findChild(QMenu)
    self.assertIsInstance(fileMenu, QMenu)
    texts = [a.text() for a in fileMenu.actions() if a.text()]
    self.assertEqual(texts, ['&New', '&Open', '&Save', 'Save &As', '&Quit'])
    window.close()

  def run_build_once(self) -> None:
    """A second 'show()' reuses the central widget rather than rebuilding."""
    window = TextWindow()
    window.show()
    QTest.qWait(50)
    first = window.centralWidget()
    window.hide()
    window.show()
    QTest.qWait(50)
    self.assertIs(window.centralWidget(), first)
    window.close()

  def run_handlers_do_not_raise(self) -> None:
    """The placeholder File-menu handlers run without error."""
    window = TextWindow()
    window.show()
    QTest.qWait(50)
    window._onNew()
    window._onOpen()
    window._onSave()
    window._onSaveAs()
    window.close()

  def run_action_without_shortcut(self) -> None:
    """The '_action' helper leaves an action unbound when given an empty
    shortcut string."""
    window = TextWindow()
    action = window._action('Plain', '', lambda *_: None)
    self.assertEqual(action.shortcut().toString(), '')
