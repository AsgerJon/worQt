"""
TextDocument subclasses 'AbstractDocument' and models a simple authored
text: an 'author', a 'title' and a 'date' (single fields), plus an ordered
array of 'sections'. Each field carries the encoder/decoder the document
layer resolves by name at save/load time. The three scalars are plain
strings, so their codecs are identity; a section encodes to its body text
and decodes back into a 'Section'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.data import AbstractDocument, SingleField, ArrayField

from ._section import Section

if TYPE_CHECKING:  # pragma: no cover
  pass


class TextDocument(AbstractDocument):
  """An authored text: author, title, date and an array of sections."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  author = SingleField[str]('')  # who wrote it
  title = SingleField[str]('')  # the document title
  date = SingleField[str]('')  # an ISO-8601 date string
  sections = ArrayField[Section]()  # the ordered body sections

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @author.setEncoder
  def _encodeAuthor(self, value: str) -> str:
    return value

  @author.setDecoder
  def _decodeAuthor(self, value: str) -> str:
    return value

  @title.setEncoder
  def _encodeTitle(self, value: str) -> str:
    return value

  @title.setDecoder
  def _decodeTitle(self, value: str) -> str:
    return value

  @date.setEncoder
  def _encodeDate(self, value: str) -> str:
    return value

  @date.setDecoder
  def _decodeDate(self, value: str) -> str:
    return value

  @sections.setEncoder
  def _encodeSection(self, section: Section) -> str:
    return section.text

  @sections.setDecoder
  def _decodeSection(self, raw: str) -> Section:
    return Section(raw)
