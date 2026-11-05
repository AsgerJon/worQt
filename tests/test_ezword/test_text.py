"""
TestText covers the EZWord text model: how text is read into words,
clauses, sentences, paragraphs and chapters, how punctuation decides
case, and that each level gives its text back.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.waitaminute.keenum import KeeResolveError

from worQt.ezword import Char, PunctNum, Word, Clause, Sentence
from worQt.ezword import Paragraph, Chapter, Part, Memoir

from . import EZWordTest


class TestText(EZWordTest):
  """Tests for the EZWord text model."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  WORDS AND CLAUSES  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_word_is_caseless(self) -> None:
    """A word is built from text of either case, from 'Char's or from
    another word, always of the same caseless characters."""
    word = Word('Hello')
    self.assertEqual([*word], [Char.H, Char.E, Char.L, Char.L, Char.O])
    self.assertEqual(str(Word('hello')), str(word))
    self.assertEqual(str(Word(Char.H, Char.I)), 'HI')
    self.assertEqual(str(Word(word)), 'HELLO')

  def test_word_refuses_what_is_no_letter(self) -> None:
    """A word holds letters only: no digits and no contractions - write
    'do not', never "don't"."""
    for text in ('r2d2', "don't", 'well-known'):
      with self.assertRaises(KeeResolveError):
        Word(text)

  def test_index_bounds(self) -> None:
    """Indexing counts from either end, and out of range is an error,
    never a wrap around."""
    word = Word('cat')
    self.assertIs(word[-1], Char.T)
    self.assertIs(word[-3], Char.C)
    for index in (3, -4):
      with self.assertRaises(IndexError):
        word[index]

  def test_clause_splits_on_whitespace(self) -> None:
    """A clause reads its words from text split on whitespace, or takes
    words and text mixed."""
    self.assertEqual(len(Clause('the quick  brown fox')), 4)
    self.assertEqual(str(Clause(Word('hi'), 'there')), 'HI THERE')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUNCTUATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_capitalize_flags(self) -> None:
    """The colon, the semicolon and the ellipsis continue in lower case;
    every other mark is followed by a capital."""
    lower = {PunctNum.COLON, PunctNum.SEMICOLON, PunctNum.ELLIPSIS}
    for mark in PunctNum:
      self.assertEqual(mark.capitalize, mark not in lower)

  def test_ellipsis_is_one_mark(self) -> None:
    """Where marks overlap, the longest wins: '...' is an ellipsis, not
    three periods."""
    self.assertIs(PunctNum.ending('wait...'), PunctNum.ELLIPSIS)
    self.assertIs(PunctNum.ending('wait.'), PunctNum.PERIOD)
    self.assertIsNone(PunctNum.ending('wait'))

  def test_sentence_ends_with_its_punctuation(self) -> None:
    """Punctuation is a feature of the sentence: a run of marks at its
    end, empty while the sentence is not ended."""
    sentence = Sentence('what ?!')
    marks = (PunctNum.QUESTION, PunctNum.EXCLAMATION)
    self.assertEqual(sentence.punctuation, marks)
    self.assertEqual(str(sentence), 'WHAT?!')
    self.assertEqual(Sentence('not ended').punctuation, ())
    self.assertEqual(Sentence(sentence).punctuation, marks)

  def test_sentence_splits_clauses_on_commas(self) -> None:
    """Within a sentence the comma separates the clauses."""
    sentence = Sentence('hello, big world.')
    self.assertEqual(len(sentence), 2)
    self.assertEqual(str(sentence), 'HELLO, BIG WORLD.')

  def test_sentence_in_text_order(self) -> None:
    """A sentence takes its clauses, then its marks, in the order the
    text has them."""
    marks = (PunctNum.QUESTION, PunctNum.EXCLAMATION)
    sentence = Sentence(Clause('hi'), 'there', *marks)
    self.assertEqual(str(sentence), 'HI, THERE?!')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARAGRAPHS AND CHAPTERS  # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_paragraph_splits_behind_punctuation(self) -> None:
    """A paragraph splits into sentences behind every run of marks."""
    paragraph = Paragraph('Wait?! Really... yes; ok')
    found = [''.join(m.value for m in s.punctuation) for s in paragraph]
    self.assertEqual(found, ['?!', '...', ';', ''])

  def test_punctuation_decides_case(self) -> None:
    """The first sentence and every sentence after a capitalizing mark
    start with a capital; all other letters are lower case."""
    text = 'HELLO, WORLD. how are you? fine; thanks... ok: yes'
    expected = 'Hello, world. How are you? Fine; thanks... ok: yes'
    self.assertEqual(str(Paragraph(text)), expected)

  def test_paragraph_round_trip(self) -> None:
    """A paragraph gives back its text, a line break inside it read as a
    space."""
    text = 'Hello, world. How are\nyou? Fine; thanks!'
    expected = 'Hello, world. How are you? Fine; thanks!'
    self.assertEqual(str(Paragraph(text)), expected)
    self.assertEqual(str(Paragraph(expected)), expected)

  def test_chapter_splits_on_blank_lines(self) -> None:
    """A chapter splits into paragraphs at blank lines, however many and
    however much whitespace they hold, and gives its text back."""
    chapter = Chapter('First one. Second?\n\n  \n\nThird, here.\n')
    self.assertEqual([len(p) for p in chapter], [2, 1])
    text = 'First one. Second?\n\nThird, here.'
    self.assertEqual(str(chapter), text)
    self.assertEqual(str(Chapter(text)), text)

  def test_part_and_memoir(self) -> None:
    """A part holds chapters and a memoir holds parts, as in LaTeX's
    'memoir'."""
    part = Part(Chapter('One. Two.'), 'Another chapter.')
    memoir = Memoir(part, Part('Lone chapter... yes.'))
    self.assertEqual([len(p) for p in memoir], [2, 1])
    self.assertEqual(str(Memoir(memoir)), str(memoir))
    lone = memoir[-1][0][0][0]  # part, chapter, paragraph, sentence
    self.assertEqual(lone.punctuation, (PunctNum.ELLIPSIS,))
