"""
VidgetTest subclasses 'WidgetTest' and is the base class for the tests
of 'worQt.vidget', with the gestures Vi needs: keys typed as they are
in 'NORMAL' mode, Esc, Enter and Ctrl+R.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.qtest import WidgetTest
from worQt.vidget import Vidget

_NO_MOD = Qt.KeyboardModifier.NoModifier
_CTRL = Qt.KeyboardModifier.ControlModifier


class VidgetTest(WidgetTest):
  """
  VidgetTest subclasses 'WidgetTest' and is the base class for the tests
  of 'worQt.vidget'.
  """

  def vidget(self, text: str = '', cursor: int = 0) -> Vidget:
    """A 'Vidget' in 'NORMAL' mode holding 'text', the cursor at
    'cursor'."""
    vidget = Vidget()
    vidget.text = text
    vidget.cursor = cursor
    return vidget

  def keys(self, vidget: Vidget, keys: str) -> None:
    """Type 'keys', one character at a time."""
    self.typeText(vidget, keys)

  def esc(self, vidget: Vidget) -> None:
    self.key(vidget, Qt.Key.Key_Escape, _NO_MOD, '\x1b')

  def enter(self, vidget: Vidget) -> None:
    self.key(vidget, Qt.Key.Key_Return, _NO_MOD, '\r')

  def backspace(self, vidget: Vidget) -> None:
    self.key(vidget, Qt.Key.Key_Backspace, _NO_MOD, '\x08')

  def redo(self, vidget: Vidget) -> None:
    self.key(vidget, Qt.Key.Key_R, _CTRL, '\x12')

  def ctrl(self, vidget: Vidget, letter: str) -> None:
    """Press Ctrl with 'letter', as Ctrl+D presses Ctrl and 'D'."""
    key = getattr(Qt.Key, 'Key_%s' % str.upper(letter))
    self.key(vidget, key, _CTRL, chr(ord(str.upper(letter)) - 64))

  def liveVidget(self, text: str, rows: int = 10) -> Vidget:
    """A 'Vidget' holding 'text', shown live and painted, about 'rows'
    rows tall, so scrolling has somewhere to go."""
    vidget = self.vidget(text)
    height = rows * vidget.font.metricsF.lineSpacing()
    vidget.resize(480, int(height) + vidget.statusHeight + 16)
    self.showLive(vidget)
    vidget.repaint()
    return vidget

  def ex(self, vidget: Vidget, command: str) -> None:
    """Write the ex command 'command' after ':' and run it."""
    self.keys(vidget, ':%s' % command)
    self.enter(vidget)
