"""
EZWord is an easy word processor.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._char import Char
from ._punct_num import PunctNum
from ._word import Word
from ._clause import Clause
from ._sentence import Sentence
from ._paragraph import Paragraph
from ._chapter import Chapter
from ._part import Part
from ._memoir import Memoir

__all__ = (
  'Char',
  'PunctNum',
  'Word',
  'Clause',
  'Sentence',
  'Paragraph',
  'Chapter',
  'Part',
  'Memoir',
)
