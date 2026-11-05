"""
Word encapsulates a single word.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import Char

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Word(BaseObject):
  """
  A Word is a single word, which is a string of characters that is
  separated by whitespace from other words. Words are the basic units
  of text, and they can be combined to form sentences, paragraphs, and
  larger bodies of text.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_chars__: Optional[tuple[Char, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getChars(self, ) -> tuple[Char, ...]:
    """Get the characters in the word."""
    if self.__pvt_chars__ is None:
      raise MissingVariable(self, '__pvt_chars__', Char)
    if isinstance(self.__pvt_chars__, tuple):
      for char in self.__pvt_chars__:
        if isinstance(char, Char):
          continue
        break
      else:
        return self.__pvt_chars__
      raise TypeException('char', char, Char)
    raise TypeException('__pvt_chars__', self.__pvt_chars__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Char]:
    """Iterate over the characters in the word."""
    yield from self._getChars()

  def __contains__(self, char: Char) -> bool:
    """Check if the word contains the given character."""
    return True if char in (*self,) else False

  def __len__(self, ) -> int:
    """Get the number of characters in the word."""
    return len(self._getChars())

  def __getitem__(self, index: int) -> Char:
    """Get the character at the given index."""
    if -len(self) <= index < len(self):
      return self._getChars()[index]
    raise IndexError('index out of range')

  def __str__(self, ) -> str:
    """Get the string representation of the word."""
    return ''.join(char.value for char in self)

  def __repr__(self, ) -> str:
    """Get the string representation of the word."""
    infoSpec: str = """%s(%s)"""
    clsName: str = type(self).__name__
    selfStr: str = str.join(', ', [str(char) for char in self])
    info = infoSpec % (clsName, selfStr)
    return info

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_chars__ = (*other,)

  @overload(str)
  def __init__(self, word: str) -> None:
    self.__pvt_chars__ = tuple(Char(str.upper(char)) for char in word)

  @overload(*ARGS[Char])
  def __init__(self, *chars: Char) -> None:
    self.__pvt_chars__ = chars
