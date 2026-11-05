"""
Chapter encapsulates a sequence of 'Paragraph' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import Paragraph

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self

#  A blank line: a line break, any whitespace (further blank lines
#  included), and another line break.
_BLANK_LINE = re.compile(r'\n\s*\n')


class Chapter(BaseObject):
  """
  A Chapter is a sequence of 'Paragraph' objects. Its text splits into
  paragraphs at every blank line.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_paragraphs__: Optional[tuple[Paragraph, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParagraphs(self, ) -> tuple[Paragraph, ...]:
    """
    The '_getParagraphs' method returns the paragraphs in the chapter.
    """
    if self.__pvt_paragraphs__ is None:
      raise MissingVariable(self, '__pvt_paragraphs__', Paragraph)
    if isinstance(self.__pvt_paragraphs__, tuple):
      for paragraph in self.__pvt_paragraphs__:
        if isinstance(paragraph, Paragraph):
          continue
        break
      else:
        return self.__pvt_paragraphs__
      raise TypeException('paragraph', paragraph, Paragraph)
    infoName = '__pvt_paragraphs__'
    raise TypeException(infoName, self.__pvt_paragraphs__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Paragraph]:
    """The '__iter__' method yields the paragraphs in the chapter."""
    yield from self._getParagraphs()

  def __contains__(self, paragraph: Paragraph) -> bool:
    """The '__contains__' method tells whether 'paragraph' is in the
    chapter."""
    return True if paragraph in (*self,) else False

  def __len__(self, ) -> int:
    """The '__len__' method returns the number of paragraphs."""
    return len(self._getParagraphs())

  def __getitem__(self, index: int) -> Paragraph:
    """The '__getitem__' method returns the paragraph at 'index'."""
    if -len(self) <= index < len(self):
      return self._getParagraphs()[index]
    raise IndexError('index out of range')

  def __str__(self, ) -> str:
    """
    The '__str__' method returns the text of the chapter, its paragraphs
    separated by blank lines.
    """
    return '\n\n'.join(str(paragraph) for paragraph in self)

  def __repr__(self, ) -> str:
    infoSpec: str = """%s(%d)"""
    return infoSpec % (type(self).__name__, id(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_paragraphs__ = (*other,)

  @overload(str)
  def __init__(self, chapter: str) -> None:
    pieces = [p for p in _BLANK_LINE.split(chapter) if str.strip(p)]
    self.__pvt_paragraphs__ = tuple(Paragraph(piece) for piece in pieces)

  @overload(*ARGS[object])
  def __init__(self, *paragraphs: Paragraph | str) -> None:
    self.__pvt_paragraphs__ = tuple(Paragraph(p) for p in paragraphs)
