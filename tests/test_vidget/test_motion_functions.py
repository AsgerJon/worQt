"""
TestMotionFunctions covers 'viMotions', the Vi motions as plain functions
of a text and a position in it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.vidget import viMotions


class TestMotionFunctions(BaseTest):
  """Tests for the Vi motions as plain functions."""

  def test_words_and_big_words(self) -> None:
    """A word is a run of letters or of other marks; a big word is any
    run of non-whitespace."""
    text = 'a.b c.d e'
    self.assertEqual(viMotions.wordForward(text, 0, 1, False), 1)
    self.assertEqual(viMotions.wordForward(text, 0, 1, True), 4)
    self.assertEqual(viMotions.wordEnd(text, 4, 1, True), 6)
    self.assertEqual(viMotions.wordBackward(text, 8, 2, True), 0)

  def test_first_non_blank(self) -> None:
    """'^' finds the first character on the line that is no space."""
    self.assertEqual(viMotions.firstNonBlank('x\n  y', 3), 4)

  def test_paragraphs(self) -> None:
    """'}' and '{' go to the blank lines around paragraphs, or to either
    end of the text."""
    text = 'a\n\nb\nc\n\nd'
    self.assertEqual(viMotions.paragraphForward(text, 0, 1), 2)
    self.assertEqual(viMotions.paragraphForward(text, 0, 2), 7)
    self.assertEqual(viMotions.paragraphForward(text, 0, 3), len(text))
    self.assertEqual(viMotions.paragraphBackward(text, 8, 1), 7)
    self.assertEqual(viMotions.paragraphBackward(text, 5, 1), 2)
    self.assertEqual(viMotions.paragraphBackward(text, 2, 1), 0)

  def test_find_in_line(self) -> None:
    """'f' and 'F' find a character on the line, 't' and 'T' stop short
    of it, and a character not there finds nothing."""
    text = 'abc,def,ghi\nx,'
    self.assertEqual(viMotions.findInLine(text, 0, ',', 2, True, False), 7)
    self.assertEqual(viMotions.findInLine(text, 0, ',', 1, True, True), 2)
    self.assertEqual(viMotions.findInLine(text, 10, ',', 1, False, True), 8)
    self.assertIsNone(viMotions.findInLine(text, 0, ',', 3, True, False))
    self.assertIsNone(viMotions.findInLine(text, 0, 'q', 1, True, False))

  def test_search_wraps(self) -> None:
    """A search finds the next occurrence either way, wrapping around
    the ends of the text, and nothing where there is none."""
    text = 'one two one'
    self.assertEqual(viMotions.search(text, 0, 'one', True), 8)
    self.assertEqual(viMotions.search(text, 8, 'one', True), 0)
    self.assertEqual(viMotions.search(text, 8, 'one', False), 0)
    self.assertEqual(viMotions.search(text, 0, 'one', False), 8)
    self.assertIsNone(viMotions.search(text, 0, 'six', True))
