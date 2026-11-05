"""
RunPageWidget covers what 'PageWidget' adds to the 'Vidget' it is: only
what the EZWord format holds goes on the page, and the page shows the
case its punctuation decides. The Vi editing itself is covered in
'tests.test_vidget'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.waitaminute import TypeException

from worQt.ezword.gui import PageWidget
from worQt.vidget import ViMode

from . import EZWordWidgetTest

_NO_MOD = Qt.KeyboardModifier.NoModifier


class RunPageWidget(EZWordWidgetTest):
  """Tests for 'PageWidget'."""

  def run_opens_in_normal_mode(self) -> None:
    """The page is Vi: it opens in 'NORMAL' mode, where keys are
    commands and type nothing."""
    page = PageWidget()
    self.assertIs(page.mode, ViMode.NORMAL)
    self.typeText(page, 'hjkl')
    self.assertEqual(page.text, '')

  def run_insert_writes_text(self) -> None:
    """Text typed in 'INSERT' mode goes on the page."""
    page = PageWidget()
    self.insert(page, 'hello, world.')
    self.assertEqual(page.text, 'hello, world.')

  def run_refuses_what_the_format_cannot_hold(self) -> None:
    """Keys for anything the format cannot hold write nothing: digits,
    apostrophes, quotes, hyphens, tabs."""
    page = PageWidget()
    self.insert(page, 'do not2\'"-\t')
    self.assertEqual(page.text, 'do not')

  def run_enter_writes_a_line_break(self) -> None:
    """Enter writes a line break; two leave a blank line, which starts a
    new paragraph."""
    page = PageWidget()
    self.typeText(page, 'ione.')
    self.key(page, Qt.Key.Key_Return, _NO_MOD, '\r')
    self.key(page, Qt.Key.Key_Enter, _NO_MOD, '\r')
    self.typeText(page, 'two')
    self.assertEqual(page.text, 'one.\n\ntwo')

  def run_shown_text_is_cased_by_punctuation(self) -> None:
    """The page shows a capital where the punctuation puts one and lower
    case elsewhere, whatever case was typed, letter for letter."""
    page = PageWidget()
    page.text = 'HELLO. world... YES; ok\n\nnext'
    shown = 'Hello. World... yes; ok\n\nNext'
    self.assertEqual(page.shownText, shown)
    self.assertEqual(len(page.shownText), len(page.text))

  def run_text_setter_refuses(self) -> None:
    """Setting text the page cannot hold, or no text at all, is
    refused."""
    page = PageWidget()
    with self.assertRaises(ValueError):
      page.text = 'version 2'
    with self.assertRaises(TypeException):
      page.text = 7
    self.assertEqual(page.text, '')

  def run_editing_modifies(self) -> None:
    """Editing marks the page modified, announcing each change once;
    setting the text is not editing it."""
    page = PageWidget()
    spy = self.spy(page.modifiedChanged)
    page.text = 'set'
    self.assertFalse(page.modified)
    self.insert(page, 'ab')
    self.assertTrue(page.modified)
    page.modified = False
    self.typeText(page, 'x')
    self.assertEqual(spy.count, 3)

  def run_paints(self) -> None:
    """The page paints, text, cursor and status line."""
    page = self.showLive(PageWidget())
    page.text = 'a page. with text, wrapping as it must.'
    page.setFocus()
    self.assertFalse(page.grab().isNull())
