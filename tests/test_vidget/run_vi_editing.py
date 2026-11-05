"""
RunViEditing covers how 'Vidget' changes its text: typing in 'INSERT'
mode and the ways into it, deleting into the register and putting it
back, and undo and redo.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.vidget import ViMode

from . import VidgetTest


class RunViEditing(VidgetTest):
  """Tests for editing in 'Vidget'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  INSERT MODE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_insert_types_until_esc(self) -> None:
    """'i' enters 'INSERT' mode, where keys type until Esc, which steps
    the cursor back onto the last character typed."""
    vidget = self.vidget()
    self.keys(vidget, 'ihello')
    self.assertIs(vidget.mode, ViMode.INSERT)
    self.assertEqual(vidget.statusLeft, '-- INSERT --')
    self.esc(vidget)
    self.assertIs(vidget.mode, ViMode.NORMAL)
    self.assertEqual(vidget.text, 'hello')
    self.assertEqual(vidget.cursor, 4)

  def run_normal_keys_do_not_type(self) -> None:
    """In 'NORMAL' mode keys are commands: they never type."""
    vidget = self.vidget('abc')
    self.keys(vidget, 'hjkl')
    self.assertEqual(vidget.text, 'abc')

  def run_ways_into_insert(self) -> None:
    """'a' types after the cursor, 'I' at the start of the line, 'A' at
    its end, 'o' on a new line below and 'O' on one above."""
    specs = (('a', 'aXbc'), ('I', 'Xabc'), ('A', 'abcX'),
             ('o', 'abc\nX'), ('O', 'X\nabc'))
    for command, expected in specs:
      vidget = self.vidget('abc', 0)
      self.keys(vidget, '%sX' % command)
      self.esc(vidget)
      self.assertEqual(vidget.text, expected, command)

  def run_insert_edits(self) -> None:
    """In 'INSERT' mode Enter writes a line break and Backspace deletes
    before the cursor."""
    vidget = self.vidget()
    self.keys(vidget, 'iab')
    self.enter(vidget)
    self.keys(vidget, 'cd')
    self.backspace(vidget)
    self.assertEqual(vidget.text, 'ab\nc')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DELETE AND PUT   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_x_and_capital_x(self) -> None:
    """'x' deletes under the cursor and 'X' before it, with a count,
    never across the line."""
    vidget = self.vidget('abcdef\ngh', 1)
    self.keys(vidget, '2x')
    self.assertEqual(vidget.text, 'adef\ngh')
    self.assertEqual(vidget.register, 'bc')
    self.keys(vidget, '9X')
    self.assertEqual(vidget.text, 'def\ngh')

  def run_dd_deletes_lines(self) -> None:
    """'dd' deletes whole lines, the last one included, leaving no empty
    line behind."""
    vidget = self.vidget('a\nb\nc', 2)
    self.keys(vidget, 'dd')
    self.assertEqual(vidget.text, 'a\nc')
    self.assertEqual(vidget.register, 'b\n')
    self.assertTrue(vidget.registerLines)
    self.keys(vidget, 'jdd')
    self.assertEqual(vidget.text, 'a')
    self.assertEqual(vidget.register, 'c\n')

  def run_d_with_a_motion(self) -> None:
    """'d' with a motion deletes from the cursor to where it lands: 'dw'
    stops at the end of the line, 'de' takes the last letter, 'd$' and
    'D' take the rest of the line."""
    specs = (('dw', 'two\nthree'), ('de', ' two\nthree'),
             ('d$', '\nthree'), ('D', '\nthree'), ('2dw', '\nthree'))
    for command, expected in specs:
      vidget = self.vidget('one two\nthree', 0)
      self.keys(vidget, command)
      self.assertEqual(vidget.text, expected, command)

  def run_put_characters(self) -> None:
    """'p' puts cut characters after the cursor and 'P' before it."""
    vidget = self.vidget('abc', 0)
    self.keys(vidget, 'xp')
    self.assertEqual(vidget.text, 'bac')
    self.keys(vidget, 'P')
    self.assertEqual(vidget.text, 'baac')

  def run_put_lines(self) -> None:
    """'p' puts cut lines below the cursor's line and 'P' above it."""
    vidget = self.vidget('a\nb', 0)
    self.keys(vidget, 'ddp')
    self.assertEqual(vidget.text, 'b\na')
    self.keys(vidget, 'ggP')
    self.assertEqual(vidget.text, 'a\nb\na')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  UNDO   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_undo_and_redo(self) -> None:
    """'u' undoes the changes one by one, an insert as one change, and
    Ctrl+R redoes them."""
    vidget = self.vidget('abc', 0)
    self.keys(vidget, 'x')
    self.keys(vidget, 'Afg')
    self.esc(vidget)
    self.assertEqual(vidget.text, 'bcfg')
    self.keys(vidget, 'u')
    self.assertEqual(vidget.text, 'bc')
    self.keys(vidget, 'u')
    self.assertEqual(vidget.text, 'abc')
    self.redo(vidget)
    self.redo(vidget)
    self.assertEqual(vidget.text, 'bcfg')

  def run_editing_modifies(self) -> None:
    """Editing marks the vidget modified; setting its text does not, and
    forgets what could be undone."""
    vidget = self.vidget('abc')
    self.assertFalse(vidget.modified)
    self.keys(vidget, 'x')
    self.assertTrue(vidget.modified)
    vidget.text = 'new'
    self.keys(vidget, 'u')
    self.assertEqual(vidget.text, 'new')
