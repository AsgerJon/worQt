"""
Clause encapsulates a sequence of 'Word' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import stringList
from worktoy.waitaminute import MissingVariable, TypeException

from . import Word

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Clause(BaseObject):
  """
  A Clause is a sequence of 'Word' objects that are grouped together to
  form a meaningful unit of text. Clauses can be used to represent
  sentences, phrases, or other linguistic structures.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_words__: Optional[tuple[Word, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getWords(self, ) -> tuple[Word, ...]:
    """Get the words in the clause."""
    if self.__pvt_words__ is None:
      raise MissingVariable(self, '__pvt_words__', Word)
    if isinstance(self.__pvt_words__, tuple):
      for word in self.__pvt_words__:
        if isinstance(word, Word):
          continue
        break
      else:
        return self.__pvt_words__
      raise TypeException('word', word, Word)
    raise TypeException('__pvt_words__', self.__pvt_words__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Word]:
    """Iterate over the words in the clause."""
    yield from self._getWords()

  def __contains__(self, word: Word) -> bool:
    """Check if a word is in the clause."""
    return True if word in (*self,) else False

  def __len__(self, ) -> int:
    """Get the number of words in the clause."""
    return len(self._getWords())

  def __getitem__(self, index: int) -> Word:
    """Get a word by index."""
    if -len(self) <= index < len(self):
      return self._getWords()[index]
    raise IndexError('Index out of range')

  def __str__(self, ) -> str:
    """Get a string representation of the clause."""
    return ' '.join(str(word) for word in self)

  def __repr__(self, ) -> str:
    infoSpec: str = """<%s: %d>"""
    clsName: str = type(self).__name__
    info: str = infoSpec % (clsName, id(self))
    return info

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_words__ = (*other,)

  @overload(str)
  def __init__(self, clause: str) -> None:
    if ' ' in clause:
      self.__init__(*str.split(clause), )
    else:
      self.__pvt_words__ = (Word(clause),)

  @overload(*ARGS[object])
  def __init__(self, *words: Word | str) -> None:
    self.__pvt_words__ = tuple(Word(word) for word in words)
