"""
RunViOperators covers the operators of 'Vidget' - 'd', 'c' and 'y' with
a motion or doubled, and their shorthands - and 'r', 'J' and '.'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.vidget import ViMode

from . import VidgetTest


class RunViOperators(VidgetTest):
  """Tests for the operators of 'Vidget'."""

  def _after(self, text: str, cursor: int, keys: str) -> str:
    """The text after typing 'keys' at 'cursor', leaving 'INSERT' mode
    if they entered it."""
    vidget = self.vidget(text, cursor)
    self.keys(vidget, keys)
    if vidget.mode is ViMode.INSERT:
      self.esc(vidget)
    return vidget.text

  def run_delete_with_finds(self) -> None:
    """'d' with 'f' takes the character found, with 't' stops short of
    it."""
    self.assertEqual(self._after('abc,def', 0, 'df,'), 'def')
    self.assertEqual(self._after('abc,def', 0, 'dt,'), ',def')

  def run_delete_over_lines(self) -> None:
    """'d' with a motion over lines takes whole lines: 'dj', 'dk', 'dG'
    and 'dgg'."""
    text = 'a\nb\nc\nd'
    self.assertEqual(self._after(text, 0, 'dj'), 'c\nd')
    self.assertEqual(self._after(text, 4, 'dk'), 'a\nd')
    self.assertEqual(self._after(text, 2, 'dG'), 'a')
    self.assertEqual(self._after(text, 4, 'dgg'), 'd')

  def run_counts_multiply(self) -> None:
    """A count before the operator and one before the motion multiply."""
    text = 'a b c d e f g'
    self.assertEqual(self._after(text, 0, '2d2w'), 'e f g')

  def run_change(self) -> None:
    """'c' deletes as 'd' does and enters 'INSERT' mode: 'cw' to the end
    of the word, 'cc' and 'S' the line's text, 'C' the rest of the line,
    's' the character."""
    self.assertEqual(self._after('one two', 0, 'cwX'), 'X two')
    self.assertEqual(self._after('a\nb\nc', 2, 'ccX'), 'a\nX\nc')
    self.assertEqual(self._after('a\nb', 0, 'SX'), 'X\nb')
    self.assertEqual(self._after('abc def', 2, 'CX'), 'abX')
    self.assertEqual(self._after('abc', 0, 'sX'), 'Xbc')
    self.assertEqual(self._after('abc,def', 0, 'ct,X'), 'X,def')

  def run_yank_and_put(self) -> None:
    """'y' copies into the register without changing the text: 'yw' a
    word, 'yy' and 'Y' whole lines."""
    vidget = self.vidget('one two', 4)
    self.keys(vidget, 'yw')
    self.assertEqual(vidget.register, 'two')
    self.assertFalse(vidget.modified)
    vidget = self.vidget('a\nb')
    self.keys(vidget, 'yyp')
    self.assertEqual(vidget.text, 'a\na\nb')
    self.keys(vidget, 'GYP')
    self.assertEqual(vidget.text, 'a\na\nb\nb')

  def run_replace(self) -> None:
    """'r' replaces under the cursor, 'count' characters with a count,
    and does nothing if the line holds not so many."""
    self.assertEqual(self._after('abc', 0, '2rX'), 'XXc')
    self.assertEqual(self._after('abc', 0, '5rX'), 'abc')

  def run_join(self) -> None:
    """'J' joins the next line on with one space, dropping its leading
    whitespace; with a count it joins that many lines."""
    self.assertEqual(self._after('one\n  two\nthree', 0, 'J'),
                     'one two\nthree')
    self.assertEqual(self._after('a\nb\nc', 0, '3J'), 'a b c')

  def run_dot_repeats_the_last_change(self) -> None:
    """'.' repeats the last change - a delete, or an insert with all it
    typed - but not a motion or a yank."""
    self.assertEqual(self._after('one two three four', 0, 'dw..'), 'four')
    vidget = self.vidget('x\ny\nz')
    self.keys(vidget, 'Aa')
    self.esc(vidget)
    self.keys(vidget, 'jyy.')
    self.assertEqual(vidget.text, 'xa\nya\nz')

  def run_one_undo_per_change(self) -> None:
    """A change, its typing included, is undone as one."""
    vidget = self.vidget('one two')
    self.keys(vidget, 'cwbig')
    self.esc(vidget)
    self.keys(vidget, 'u')
    self.assertEqual(vidget.text, 'one two')
