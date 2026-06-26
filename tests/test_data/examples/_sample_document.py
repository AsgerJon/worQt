"""
SampleDocument subclasses 'AbstractDocument' from 'worQt.data' and
provides a sample document for testing purposes.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.lorem_ipsum import Paragraph
from worktoy.utilities import wordWrap, textFmt

from ..examples import SampleFile
from worQt.data import AbstractDocument, SingleField

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional, TypeAlias


class SampleDocument(AbstractDocument):
  """
  SampleDocument subclasses 'AbstractDocument' from 'worQt.data' and
  provides a sample document for testing purposes.
  """

  mainFile = AttriBox[SampleFile]('sample_document.tmp')
  titleField = SingleField[str]('Sample Document')
  numberField = SingleField[int](69)
  textField = SingleField[Paragraph](Paragraph(600))

  @titleField.setEncoder
  def _encodeTitleField(self, value: str) -> str:
    return value

  @titleField.setDecoder
  def _decodeTitleField(self, value: str) -> str:
    return value

  @numberField.setEncoder
  def _encodeNumberField(self, value: int) -> str:
    return str(value)

  @numberField.setDecoder
  def _decodeNumberField(self, value: str) -> int:
    return int(value)

  @textField.setEncoder
  def _encodeTextField(self, paragraph: Paragraph) -> str:
    return """%s%s""" % (os.linesep, wordWrap(77, paragraph.realize()))

  @textField.setDecoder
  def _decodeTextField(self, value: str) -> Paragraph:
    return Paragraph(len(textFmt(value)))
