"""
Memoir encapsulates a sequence of 'Part' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import Part

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Memoir(BaseObject):
  """
  A Memoir is a sequence of 'Part' objects, named for the LaTeX 'memoir'
  class it follows: the memoir holds parts, a part holds chapters.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_parts__: Optional[tuple[Part, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple[Part, ...]:
    """
    The '_getParts' method returns the parts in the memoir.
    """
    if self.__pvt_parts__ is None:
      raise MissingVariable(self, '__pvt_parts__', Part)
    if isinstance(self.__pvt_parts__, tuple):
      for part in self.__pvt_parts__:
        if isinstance(part, Part):
          continue
        break
      else:
        return self.__pvt_parts__
      raise TypeException('part', part, Part)
    raise TypeException('__pvt_parts__', self.__pvt_parts__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Part]:
    """The '__iter__' method yields the parts in the memoir."""
    yield from self._getParts()

  def __contains__(self, part: Part) -> bool:
    """The '__contains__' method tells whether 'part' is in the memoir."""
    return True if part in (*self,) else False

  def __len__(self, ) -> int:
    """The '__len__' method returns the number of parts."""
    return len(self._getParts())

  def __getitem__(self, index: int) -> Part:
    """The '__getitem__' method returns the part at 'index'."""
    if -len(self) <= index < len(self):
      return self._getParts()[index]
    raise IndexError('index out of range')

  def __str__(self, ) -> str:
    """
    The '__str__' method returns the text of the memoir, its parts
    separated by blank lines. Until parts have headings, the part
    boundaries do not survive in the text.
    """
    return '\n\n'.join(str(part) for part in self)

  def __repr__(self, ) -> str:
    infoSpec: str = """%s(%d)"""
    return infoSpec % (type(self).__name__, id(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_parts__ = (*other,)

  @overload(*ARGS[object])
  def __init__(self, *parts: Part | str) -> None:
    self.__pvt_parts__ = tuple(Part(part) for part in parts)
