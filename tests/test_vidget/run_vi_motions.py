"""
RunViMotions covers the 'NORMAL' mode motions of 'Vidget': characters,
words and big words, lines and line ends, the whole text, paragraphs,
finds on the line and searches, with counts, and that the cursor stays
on a character.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.vidget import ViMode

from . import VidgetTest


class RunViMotions(VidgetTest):
  """Tests for the motions of 'Vidget'."""

  def run_starts_in_normal_mode(self) -> None:
    """A vidget starts in 'NORMAL' mode, with the cursor at the start."""
    vidget = self.vidget('hello')
    self.assertIs(vidget.mode, ViMode.NORMAL)
    self.assertEqual(vidget.cursor, 0)

  def run_h_and_l_stay_on_the_line(self) -> None:
    """'h' and 'l' move along the line, never past either end of it."""
    vidget = self.vidget('ab\ncd', 3)
    self.keys(vidget, 'l')
    self.assertEqual(vidget.cursor, 4)
    self.keys(vidget, 'l')
    self.assertEqual(vidget.cursor, 4)
    self.keys(vidget, 'hh')
    self.assertEqual(vidget.cursor, 3)

  def run_counts(self) -> None:
    """A count repeats a motion; a lone '0' is a motion, not a count."""
    vidget = self.vidget('abcdefgh', 0)
    self.keys(vidget, '3l')
    self.assertEqual(vidget.cursor, 3)
    self.keys(vidget, '10l')
    self.assertEqual(vidget.cursor, 7)
    self.keys(vidget, '0')
    self.assertEqual(vidget.cursor, 0)

  def run_j_and_k_keep_the_column(self) -> None:
    """'j' and 'k' move between lines, keeping the column as far as the
    line allows."""
    vidget = self.vidget('abcd\nab\nabcd', 3)
    self.keys(vidget, 'j')
    self.assertEqual(vidget.cursor, 6)
    self.keys(vidget, 'j')
    self.assertEqual(vidget.cursor, 9)
    self.keys(vidget, '2k')
    self.assertEqual(vidget.cursor, 1)

  def run_word_motions(self) -> None:
    """'w' goes to the next word, 'e' to the end of one and 'b' back to
    the start of one; punctuation is a word of its own."""
    vidget = self.vidget('one two, three')
    self.keys(vidget, 'w')
    self.assertEqual(vidget.cursor, 4)
    self.keys(vidget, 'w')
    self.assertEqual(vidget.cursor, 7)
    self.keys(vidget, 'e')
    self.assertEqual(vidget.cursor, 13)
    self.keys(vidget, '2b')
    self.assertEqual(vidget.cursor, 7)

  def run_line_ends(self) -> None:
    """'0' and '$' go to the first and the last character of the
    line."""
    vidget = self.vidget('one\ntwo three', 6)
    self.keys(vidget, '$')
    self.assertEqual(vidget.cursor, 12)
    self.keys(vidget, '0')
    self.assertEqual(vidget.cursor, 4)

  def run_gg_and_g(self) -> None:
    """'gg' goes to the first line and 'G' to the last, or to the line
    a count names."""
    vidget = self.vidget('a\nb\nc\nd', 0)
    self.keys(vidget, 'G')
    self.assertEqual(vidget.cursor, 6)
    self.keys(vidget, 'gg')
    self.assertEqual(vidget.cursor, 0)
    self.keys(vidget, '3G')
    self.assertEqual(vidget.cursor, 4)

  def run_first_non_blank_and_big_words(self) -> None:
    """'^' goes to the first character that is no space; 'W', 'B' and
    'E' move by runs of non-whitespace."""
    vidget = self.vidget('  a.b c.d', 8)
    self.keys(vidget, '^')
    self.assertEqual(vidget.cursor, 2)
    self.keys(vidget, 'W')
    self.assertEqual(vidget.cursor, 6)
    self.keys(vidget, 'B')
    self.assertEqual(vidget.cursor, 2)
    self.keys(vidget, 'E')
    self.assertEqual(vidget.cursor, 4)

  def run_finds(self) -> None:
    """'f', 't', 'F' and 'T' find a character on the line; ';' finds
    it again and ',' the other way."""
    vidget = self.vidget('abc,def,ghi')
    self.keys(vidget, 'f,')
    self.assertEqual(vidget.cursor, 3)
    self.keys(vidget, ';')
    self.assertEqual(vidget.cursor, 7)
    self.keys(vidget, ',')
    self.assertEqual(vidget.cursor, 3)
    self.keys(vidget, '$F,')
    self.assertEqual(vidget.cursor, 7)
    self.keys(vidget, '0t,')
    self.assertEqual(vidget.cursor, 2)
    self.keys(vidget, 'fz')
    self.assertEqual(vidget.cursor, 2)

  def run_paragraphs(self) -> None:
    """'}' and '{' go to the blank lines around paragraphs."""
    vidget = self.vidget('a\n\nb\nc\n\nd')
    self.keys(vidget, '}')
    self.assertEqual(vidget.cursor, 2)
    self.keys(vidget, '}')
    self.assertEqual(vidget.cursor, 7)
    self.keys(vidget, '{')
    self.assertEqual(vidget.cursor, 2)

  def run_search(self) -> None:
    """'/' searches forward and '?' back, 'n' finds the same again and
    'N' the other way, wrapping around the ends of the text."""
    vidget = self.vidget('cat dog cat dog')
    self.keys(vidget, '/dog')
    self.enter(vidget)
    self.assertEqual(vidget.cursor, 4)
    self.keys(vidget, 'n')
    self.assertEqual(vidget.cursor, 12)
    self.keys(vidget, 'n')
    self.assertEqual(vidget.cursor, 4)
    self.keys(vidget, 'N')
    self.assertEqual(vidget.cursor, 12)
    self.keys(vidget, '?cat')
    self.enter(vidget)
    self.assertEqual(vidget.cursor, 8)

  def run_search_for_the_word_under_the_cursor(self) -> None:
    """'*' searches forward for the word under the cursor, '#' back."""
    vidget = self.vidget('cat dog cat dog')
    self.keys(vidget, '*')
    self.assertEqual(vidget.cursor, 8)
    self.keys(vidget, '#')
    self.assertEqual(vidget.cursor, 0)

  def run_search_not_found(self) -> None:
    """A search that finds nothing says so and leaves the cursor."""
    vidget = self.vidget('cat dog', 2)
    self.keys(vidget, '/cow')
    self.enter(vidget)
    self.assertEqual(vidget.statusLeft, 'Pattern not found: cow')
    self.assertEqual(vidget.cursor, 2)

  def run_pending_keys(self) -> None:
    """A command not yet complete waits on the status line; Esc drops
    it, as does a key that completes nothing."""
    vidget = self.vidget('abc')
    self.keys(vidget, '2d')
    self.assertEqual(vidget.pendingKeys, '2d')
    self.assertEqual(vidget.statusLeft, '2d')
    self.esc(vidget)
    self.assertEqual(vidget.pendingKeys, '')
    self.keys(vidget, 'dq')
    self.assertEqual(vidget.pendingKeys, '')
    self.assertEqual(vidget.text, 'abc')

  def run_ruler(self) -> None:
    """The status line shows the cursor's line and column, from 1."""
    vidget = self.vidget('ab\ncd', 4)
    self.assertEqual(vidget.statusRight, '2,2')
