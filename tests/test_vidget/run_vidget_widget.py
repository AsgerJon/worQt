"""
RunVidgetWidget covers 'Vidget' as a widget: what it accepts, the cursor
it draws, the mouse and the focus - no trap: a click puts the cursor
where it lands in any mode, and the focus moves away as anywhere else -
and that it paints.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QWidget, QVBoxLayout
from worktoy.waitaminute import TypeException

from worQt.vidget import Vidget, ViMode

from . import VidgetTest


class RunVidgetWidget(VidgetTest):
  """Tests for 'Vidget' as a widget."""

  def _textCorner(self, vidget: Vidget) -> QPoint:
    """A point just inside the top left corner of the text, right of
    the line numbers."""
    inset = 0
    for dims in (vidget.marginsDims, vidget.bordersDims,
                 vidget.paddingsDims):
      inset += dims.left
    return QPoint(inset + vidget.gutterWidth + 1, inset + 4)

  def run_accepts_printable_text(self) -> None:
    """A vidget takes printable characters and line breaks; setting any
    other text, or no text at all, is refused."""
    vidget = self.vidget()
    self.assertTrue(vidget.accepts('x'))
    self.assertTrue(vidget.accepts('\n'))
    self.assertFalse(vidget.accepts('\x07'))
    self.assertFalse(vidget.accepts('xy'))
    with self.assertRaises(ValueError):
      vidget.text = 'bell\x07'
    with self.assertRaises(TypeException):
      vidget.text = 7

  def run_cursor_shape(self) -> None:
    """The cursor is a block in 'NORMAL' mode and a bar in 'INSERT'."""
    vidget = self.vidget('abc')
    self.assertTrue(vidget.blockCursor)
    self.keys(vidget, 'i')
    self.assertFalse(vidget.blockCursor)

  def run_click_places_the_cursor_in_any_mode(self) -> None:
    """A click takes the focus and puts the cursor where it lands, in
    'NORMAL' and 'INSERT' mode alike, and gives up an ex command.

    The focus is read as the window's focus widget, not 'hasFocus', which
    holds only while the window is the active one - and a desktop that
    refuses to let a test window steal the activation is right to."""
    vidget = self.showLive(self.vidget('hello world', 6))
    for keys in ('', 'A', ':w'):
      self.keys(vidget, keys)
      self.click(vidget, self._textCorner(vidget))
      self.assertEqual(vidget.cursor, 0, keys)
      self.assertIs(vidget.focusWidget(), vidget, keys)
      self.esc(vidget)
      vidget.cursor = 6
    self.assertIs(vidget.mode, ViMode.NORMAL)

  def run_focus_moves_away(self) -> None:
    """No trap: a click on another widget takes the focus from the
    vidget, in any mode, and the vidget stops drawing its cursor. The
    focus is read as the window's focus widget, as above."""
    host = QWidget()
    layout = QVBoxLayout(host)
    vidget, other = self.vidget('abc'), Vidget()
    layout.addWidget(vidget)
    layout.addWidget(other)
    self.showLive(host)
    self.click(vidget, self._textCorner(vidget))
    self.keys(vidget, 'i')
    self.assertIs(host.focusWidget(), vidget)
    self.click(other, self._textCorner(other))
    self.assertIs(host.focusWidget(), other)
    self.assertFalse(vidget.showsCursor())
    self.assertIs(vidget.mode, ViMode.INSERT)

  def run_unused_keys_pass_on(self) -> None:
    """A key the mode has no use for is passed on to the parent, so
    shortcuts and menus keep working."""
    vidget = self.vidget('abc')
    self.key(vidget, Qt.Key.Key_F5, Qt.KeyboardModifier.NoModifier, '')
    self.assertEqual(vidget.text, 'abc')

  def run_eighty_columns(self) -> None:
    """A vidget is never narrower than 80 characters beside its line
    numbers, and the gutter growing widens it."""
    vidget = self.vidget()
    textWidth = vidget.font.metricsF.horizontalAdvance('0' * 80)
    least = vidget.minimumSizeHint().width()
    self.assertGreaterEqual(least, textWidth + vidget.gutterWidth)
    vidget.text = '\n' * 12345
    self.assertGreater(vidget.minimumSizeHint().width(), least)

  def run_paints(self) -> None:
    """The vidget paints, status line, text and cursor."""
    vidget = self.showLive(self.vidget('some text, wrapping as it must.'))
    vidget.setFocus()
    self.assertFalse(vidget.grab().isNull())
