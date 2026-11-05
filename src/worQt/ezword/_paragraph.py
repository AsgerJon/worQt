"""
Paragraph encapsulates a sequence of 'Sentence' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import PunctNum, Sentence

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Paragraph(BaseObject):
  """
  A Paragraph is a sequence of 'Sentence' objects. Its text splits into
  sentences behind every run of 'PunctNum' marks, such as '.' or '?!',
  each run staying with the sentence it ends: punctuation is a feature
  of the sentence.

  Punctuation decides case, so the paragraph is where case is decided:
  its first sentence, and every sentence after punctuation whose last
  mark has 'capitalize' True, starts with a capital letter; every other
  letter is lower case.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_sentences__: Optional[tuple[Sentence, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getSentences(self, ) -> tuple[Sentence, ...]:
    """
    The '_getSentences' method returns the sentences in the paragraph.
    """
    if self.__pvt_sentences__ is None:
      raise MissingVariable(self, '__pvt_sentences__', Sentence)
    if isinstance(self.__pvt_sentences__, tuple):
      for sentence in self.__pvt_sentences__:
        if isinstance(sentence, Sentence):
          continue
        break
      else:
        return self.__pvt_sentences__
      raise TypeException('sentence', sentence, Sentence)
    raise TypeException('__pvt_sentences__', self.__pvt_sentences__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Sentence]:
    """The '__iter__' method yields the sentences in the paragraph."""
    yield from self._getSentences()

  def __contains__(self, sentence: Sentence) -> bool:
    """The '__contains__' method tells whether 'sentence' is in the
    paragraph."""
    return True if sentence in (*self,) else False

  def __len__(self, ) -> int:
    """The '__len__' method returns the number of sentences."""
    return len(self._getSentences())

  def __getitem__(self, index: int) -> Sentence:
    """The '__getitem__' method returns the sentence at 'index'."""
    if -len(self) <= index < len(self):
      return self._getSentences()[index]
    raise IndexError('index out of range')

  def __str__(self, ) -> str:
    """
    The '__str__' method returns the text of the paragraph, cased by its
    punctuation.
    """
    out, capitalize = [], True
    for sentence in self:
      text = str.lower(str(sentence))
      out.append(str.capitalize(text) if capitalize else text)
      punctuation = sentence.punctuation
      capitalize = punctuation[-1].capitalize if punctuation else True
    return ' '.join(out)

  def __repr__(self, ) -> str:
    infoSpec: str = """%s(%d)"""
    return infoSpec % (type(self).__name__, id(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_sentences__ = (*other,)

  @overload(str)
  def __init__(self, paragraph: str) -> None:
    #  Inside a paragraph a line break is only whitespace: blank lines
    #  separate paragraphs, which is for the chapter to split on.
    text = ' '.join(str.split(paragraph))
    marks = [char for mark in PunctNum for char in mark.value]
    pieces, current = [], ''
    for char in text:
      if char not in marks and current and current[-1] in marks:
        pieces.append(current)
        current = ''
      current += char
    if str.strip(current):
      pieces.append(current)
    self.__pvt_sentences__ = tuple(Sentence(piece) for piece in pieces)

  @overload(*ARGS[object])
  def __init__(self, *sentences: Sentence | str) -> None:
    self.__pvt_sentences__ = tuple(Sentence(s) for s in sentences)
