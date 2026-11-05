"""
Sentence encapsulates a sequence of Clause objects ended by its
punctuation.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import Clause, PunctNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Sentence(BaseObject):
  """
  A Sentence is a sequence of Clause objects that are grouped together to
  form a complete thought or idea. Sentences can be used to convey
  information, express opinions, or tell stories.

  Within a sentence the comma separates the clauses. Punctuation is a
  feature of the sentence: it ends with its 'punctuation', a run of
  'PunctNum' members such as '?!' or '...', which is empty for a
  sentence not ended yet.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_clauses__: Optional[tuple[Clause, ...]] = None
  __pvt_punctuation__: Optional[tuple[PunctNum, ...]] = None

  #  Virtual Variables
  punctuation: Field[tuple[PunctNum, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getClauses(self, ) -> tuple[Clause, ...]:
    """Get the clauses in the sentence."""
    if self.__pvt_clauses__ is None:
      raise MissingVariable(self, '__pvt_clauses__', Clause)
    if isinstance(self.__pvt_clauses__, tuple):
      for clause in self.__pvt_clauses__:
        if isinstance(clause, Clause):
          continue
        break
      else:
        return self.__pvt_clauses__
      raise TypeException('clause', clause, Clause)
    raise TypeException('__pvt_clauses__', self.__pvt_clauses__, tuple)

  @punctuation.GET
  def _getPunctuation(self, ) -> tuple[PunctNum, ...]:
    """
    The 'punctuation' getter returns the marks ending the sentence, in
    order, or an empty tuple for a sentence not ended yet.
    """
    if self.__pvt_punctuation__ is None:
      return ()
    return self.__pvt_punctuation__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Clause]:
    """Iterate over the clauses in the sentence."""
    yield from self._getClauses()

  def __contains__(self, clause: Clause) -> bool:
    """Check if a clause is in the sentence."""
    return True if clause in (*self,) else False

  def __len__(self, ) -> int:
    """Get the number of clauses in the sentence."""
    return len(self._getClauses())

  def __getitem__(self, index: int) -> Clause:
    """Get the clause at the given index."""
    if -len(self) <= index < len(self):
      return self._getClauses()[index]
    raise IndexError('index out of range')

  def __str__(self) -> str:
    """Get the string representation of the sentence."""
    text = ', '.join(str(clause) for clause in self)
    return text + ''.join(mark.value for mark in self.punctuation)

  def __repr__(self) -> str:
    """Get the string representation of the sentence."""
    infoSpec: str = """%s(%d)"""
    return infoSpec % (type(self).__name__, id(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_clauses__ = (*other,)
    self.__pvt_punctuation__ = other.punctuation

  @overload(str)
  def __init__(self, sentence: str) -> None:
    text, punctuation = str.strip(sentence), []
    mark = PunctNum.ending(text)
    while mark is not None:
      punctuation.insert(0, mark)
      text = str.rstrip(text[:-len(mark.value)])
      mark = PunctNum.ending(text)
    self.__pvt_punctuation__ = (*punctuation,)
    if not str.strip(text):
      self.__pvt_clauses__ = ()
      return
    clauses = str.split(text, ',')
    self.__pvt_clauses__ = tuple(Clause(str.strip(c)) for c in clauses)

  @overload(*ARGS[object])
  def __init__(self, *clauses: Clause | str | PunctNum) -> None:
    items, punctuation = [*clauses, ], []
    while items and isinstance(items[-1], PunctNum):
      punctuation.insert(0, items.pop())
    self.__pvt_punctuation__ = (*punctuation,)
    self.__pvt_clauses__ = tuple(Clause(clause) for clause in items)
