"""
RunViCommandLine covers the 'COMMAND' mode of 'Vidget': writing an ex
command after ':' or a search after '/' or '?' on the status line, line
numbers, and what ':w', ':q', ':wq', ':x', ':q!', 'ZZ' and 'ZQ' ask of
the window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.vidget import ViMode

from . import VidgetTest


class RunViCommandLine(VidgetTest):
  """Tests for the ex commands of 'Vidget'."""

  def run_colon_writes_on_the_status_line(self) -> None:
    """':' enters 'COMMAND' mode; the command is written on the status
    line, and the text cursor is not drawn meanwhile."""
    vidget = self.vidget('abc')
    self.keys(vidget, ':wq')
    self.assertIs(vidget.mode, ViMode.COMMAND)
    self.assertEqual(vidget.statusLeft, ':wq')
    self.assertEqual(vidget.text, 'abc')
    self.assertFalse(vidget.showsCursor())

  def run_esc_and_backspace_leave(self) -> None:
    """Esc gives the command up; Backspace deletes from it, and leaves
    once it is empty."""
    vidget = self.vidget()
    self.keys(vidget, ':ab')
    self.esc(vidget)
    self.assertIs(vidget.mode, ViMode.NORMAL)
    self.keys(vidget, ':a')
    self.backspace(vidget)
    self.assertIs(vidget.mode, ViMode.COMMAND)
    self.backspace(vidget)
    self.assertIs(vidget.mode, ViMode.NORMAL)

  def run_write(self) -> None:
    """':w' asks for the text to be written."""
    vidget = self.vidget()
    spy = self.spy(vidget.writeRequested)
    self.ex(vidget, 'w')
    self.assertEqual(spy.count, 1)
    self.assertIs(vidget.mode, ViMode.NORMAL)

  def run_quit_refuses_unsaved_changes(self) -> None:
    """':q' asks to quit, but refuses while there are unsaved changes,
    as Vi does; ':q!' throws them away and quits."""
    vidget = self.vidget('abc')
    spy = self.spy(vidget.quitRequested)
    self.keys(vidget, 'x')
    self.ex(vidget, 'q')
    self.assertEqual(spy.count, 0)
    self.assertIn('No write since last change', vidget.statusLeft)
    self.ex(vidget, 'q!')
    self.assertEqual(spy.count, 1)
    self.assertFalse(vidget.modified)

  def run_write_and_quit(self) -> None:
    """':wq' and ':x' ask for the text to be written, then to quit."""
    for command in ('wq', 'x'):
      vidget = self.vidget()
      writes = self.spy(vidget.writeRequested)
      quits = self.spy(vidget.quitRequested)
      self.ex(vidget, command)
      self.assertEqual((writes.count, quits.count), (1, 1), command)

  def run_line_numbers(self) -> None:
    """':' with a line number goes to that line, ':$' to the last."""
    vidget = self.vidget('l1\nl2\n  l3\nl4')
    self.ex(vidget, '3')
    self.assertEqual(vidget.cursor, 8)
    self.ex(vidget, '$')
    self.assertEqual(vidget.cursor, 11)

  def run_zz_and_zq(self) -> None:
    """'ZZ' writes and quits, as ':x' does; 'ZQ' quits, throwing
    unsaved changes away, as ':q!' does."""
    vidget = self.vidget('abc')
    writes = self.spy(vidget.writeRequested)
    quits = self.spy(vidget.quitRequested)
    self.keys(vidget, 'ZZ')
    self.assertEqual((writes.count, quits.count), (1, 1))
    self.keys(vidget, 'xZQ')
    self.assertEqual((writes.count, quits.count), (1, 2))
    self.assertFalse(vidget.modified)

  def run_tab_commands(self) -> None:
    """'gt' and ':tabn' ask for the next tab, 'gT' and ':tabp' for the
    previous one, ':tabnew' for a new one."""
    vidget = self.vidget()
    steps = self.spy(vidget.tabStepRequested)
    news = self.spy(vidget.newTabRequested)
    self.keys(vidget, 'gt')
    self.keys(vidget, 'gT')
    self.ex(vidget, 'tabn')
    self.ex(vidget, 'tabp')
    self.ex(vidget, 'tabnew')
    self.assertEqual(steps.emissions, [(1,), (-1,), (1,), (-1,)])
    self.assertEqual(news.count, 1)

  def run_search_prompt(self) -> None:
    """'/' and '?' open the command line with their own prompt."""
    vidget = self.vidget()
    self.keys(vidget, '/ab')
    self.assertEqual(vidget.statusLeft, '/ab')
    self.esc(vidget)
    self.keys(vidget, '?cd')
    self.assertEqual(vidget.statusLeft, '?cd')

  def run_unknown_command(self) -> None:
    """A command the vidget does not know leaves a message, which the
    next key clears."""
    vidget = self.vidget()
    self.ex(vidget, 'nope')
    self.assertEqual(vidget.statusLeft, 'Not an editor command: nope')
    self.keys(vidget, 'l')
    self.assertEqual(vidget.statusLeft, '')
