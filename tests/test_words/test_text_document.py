"""
TestTextDocument subclasses 'WordsTest' and covers the 'worQt.words' data
model: the single fields ('author', 'title', 'date'), the 'sections' array
of 'Section' items, their save/load round-trip, and the in-place change
notification chain from a 'Section' back to its owning field.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worQt.data import AbstractDocument, ArrayField, ArrayLike
from worQt.words import Section, TextDocument

from . import WordsTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class SpySectionField(ArrayField):
  """An 'ArrayField' recording each 'notifyChange', so a test can observe
  the section -> field change chain."""

  calls = []  # documents notified; class-level, cleared per test

  def notifyChange(self, doc: Any) -> None:
    type(self).calls.append(doc)


class SpyDoc(AbstractDocument):
  """A document whose section array records change notifications."""

  sections = SpySectionField[Section]()


class TestTextDocument(WordsTest):
  """Covers the text document fields, persistence and notify chain."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  HELPERS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _doc(self, name: str = 'sample.json') -> TextDocument:
    """A 'TextDocument' whose file is pinned inside the temp dir."""
    document = TextDocument()
    document.mainFile.filePath = os.path.join(self.tempDir.directory, name)
    return document

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DEFAULTS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_scalar_defaults(self) -> None:
    """A fresh document has empty author, title and date."""
    document = self._doc()
    self.assertEqual(document.author, '')
    self.assertEqual(document.title, '')
    self.assertEqual(document.date, '')

  def test_sections_default_empty(self) -> None:
    """A fresh document has an empty 'sections' array."""
    document = self._doc()
    self.assertIsInstance(document.sections, ArrayLike)
    self.assertEqual(len(document.sections), 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SECTIONS (in memory)   # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_section_text(self) -> None:
    """A 'Section' built from a string carries that text."""
    section = Section('hello')
    self.assertEqual(section.text, 'hello')

  def test_sections_append_keeps_order(self) -> None:
    """Appended sections keep insertion order."""
    document = self._doc()
    document.sections.append(Section('first'))
    document.sections.append(Section('second'))
    texts = [section.text for section in document.sections]
    self.assertEqual(texts, ['first', 'second'])

  def test_sections_per_document_independence(self) -> None:
    """Each document owns its own section array."""
    first = self._doc('first.json')
    second = self._doc('second.json')
    first.sections.append(Section('only here'))
    self.assertEqual(len(first.sections), 1)
    self.assertEqual(len(second.sections), 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SAVE / LOAD   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_scalars_round_trip(self) -> None:
    """The single fields survive a save/load round-trip."""
    document = self._doc()
    document.author = 'Asger'
    document.title = 'Never gonna give you up'
    document.date = '2026-06-07'
    document.save()

    other = self._doc()
    other.load()
    self.assertEqual(other.author, 'Asger')
    self.assertEqual(other.title, 'Never gonna give you up')
    self.assertEqual(other.date, '2026-06-07')

  def test_sections_round_trip(self) -> None:
    """The section array survives a save/load round-trip, in order."""
    document = self._doc()
    document.sections.append(Section('alpha'))
    document.sections.append(Section('beta'))
    document.save()

    other = self._doc()
    other.load()
    texts = [section.text for section in other.sections]
    self.assertEqual(texts, ['alpha', 'beta'])

  def test_empty_document_round_trips(self) -> None:
    """An untouched document saves and loads without error, staying empty."""
    document = self._doc()
    document.save()
    self.assertTrue(os.path.exists(document.mainFile.filePath))

    other = self._doc()
    other.load()
    self.assertEqual(other.author, '')
    self.assertEqual(len(other.sections), 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFY CHAIN   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_section_edit_notifies_owning_field(self) -> None:
    """Editing a section already held by a document fires the field hook."""
    SpySectionField.calls.clear()
    document = SpyDoc()
    section = Section('before')
    document.sections.append(section)  # adopts the section
    SpySectionField.calls.clear()  # drop the append's own notification
    section.text = 'after'  # the in-place edit under test
    self.assertTrue(SpySectionField.calls)
    self.assertIs(SpySectionField.calls[-1], document)

  def test_unowned_section_edit_is_silent(self) -> None:
    """Editing a section not yet in any document is a no-op, not a crash."""
    SpySectionField.calls.clear()
    section = Section('loose')  # never added: no owner
    section.text = 'changed'
    self.assertEqual(SpySectionField.calls, [])
    self.assertEqual(section.text, 'changed')
