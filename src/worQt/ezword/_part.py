"""
Part encapsulates a sequence of 'Chapter' objects.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS, ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

from . import Chapter

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Iterator, Self


class Part(BaseObject):
  """
  A Part is a sequence of 'Chapter' objects, as the '\\part' of a LaTeX
  'memoir' groups its chapters.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __pvt_chapters__: Optional[tuple[Chapter, ...]] = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getChapters(self, ) -> tuple[Chapter, ...]:
    """
    The '_getChapters' method returns the chapters in the part.
    """
    if self.__pvt_chapters__ is None:
      raise MissingVariable(self, '__pvt_chapters__', Chapter)
    if isinstance(self.__pvt_chapters__, tuple):
      for chapter in self.__pvt_chapters__:
        if isinstance(chapter, Chapter):
          continue
        break
      else:
        return self.__pvt_chapters__
      raise TypeException('chapter', chapter, Chapter)
    raise TypeException('__pvt_chapters__', self.__pvt_chapters__, tuple)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[Chapter]:
    """The '__iter__' method yields the chapters in the part."""
    yield from self._getChapters()

  def __contains__(self, chapter: Chapter) -> bool:
    """The '__contains__' method tells whether 'chapter' is in the
    part."""
    return True if chapter in (*self,) else False

  def __len__(self, ) -> int:
    """The '__len__' method returns the number of chapters."""
    return len(self._getChapters())

  def __getitem__(self, index: int) -> Chapter:
    """The '__getitem__' method returns the chapter at 'index'."""
    if -len(self) <= index < len(self):
      return self._getChapters()[index]
    raise IndexError('index out of range')

  def __str__(self, ) -> str:
    """
    The '__str__' method returns the text of the part, its chapters
    separated by blank lines. Until chapters have headings, the chapter
    boundaries do not survive in the text.
    """
    return '\n\n'.join(str(chapter) for chapter in self)

  def __repr__(self, ) -> str:
    infoSpec: str = """%s(%d)"""
    return infoSpec % (type(self).__name__, id(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(THIS)
  def __init__(self, other: Self) -> None:
    self.__pvt_chapters__ = (*other,)

  @overload(*ARGS[object])
  def __init__(self, *chapters: Chapter | str) -> None:
    self.__pvt_chapters__ = tuple(Chapter(c) for c in chapters)
