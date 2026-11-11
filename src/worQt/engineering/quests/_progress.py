"""
Progress is how far a player has come: the quests done, and so the
parts unlocked.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from pathlib import Path

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from ..circuits import KINDS, LOGIC, SPECS
from ._quests import QUESTS, STARTING


class Progress(BaseObject):
  """
  Progress is how far a player has come along the quests: 'done', the
  names of the quests reached, in their order. 'unlocked' are the kinds
  of part the player may add: a wire, a source and a lamp from the
  start, and each reward of a quest done. A quest is 'open' once each
  before it is done; 'withDone' returns the progress with one more.

  'str()' is the text kept on disk, a quest's name a line, read back by
  'Progress(text)', names of no quest passed over; 'load' reads a file,
  nothing done if there is none, and 'save' writes one.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __progress_done__: tuple[str, ...] = ()

  #  Virtual Variables
  done: Field[tuple[str, ...]] = Field()
  unlocked: Field[tuple[type, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @done.GET
  def _getDone(self, ) -> tuple[str, ...]:
    """The 'done' getter returns the names of the quests done, in their
    order."""
    return self.__progress_done__

  @unlocked.GET
  def _getUnlocked(self, ) -> tuple:
    """The 'unlocked' getter returns what the player may add: kinds of
    part, in the order of the kinds, the logic parts, then the kinds of
    chip by their names, in the order of the chips."""
    kinds = {*STARTING}
    for quest in QUESTS:
      if quest.name in self.done:
        kinds.update(quest.reward)
    order = (*KINDS, *LOGIC, *SPECS)
    return (*[kind for kind in order if kind in kinds],)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    return ''.join('%s\n' % name for name in self.done)

  def __repr__(self, ) -> str:
    return '%s(%d of %d quests done)' % (type(self).__name__,
                                         len(self.done), len(QUESTS))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(str)
  def __init__(self, text: str) -> None:
    names = {line.strip() for line in text.splitlines()}
    self.__progress_done__ = (*[quest.name for quest in QUESTS
                                if quest.name in names],)

  @overload()
  def __init__(self, ) -> None:
    self.__progress_done__ = ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def isDone(self, index: int) -> bool:
    """The 'isDone' method tells whether the quest of 'index' is done."""
    return True if QUESTS[index].name in self.done else False

  def isOpen(self, index: int) -> bool:
    """The 'isOpen' method tells whether the quest of 'index' may be
    played: each quest before it done."""
    return all(self.isDone(before) for before in range(index))

  def withDone(self, index: int) -> Progress:
    """The 'withDone' method returns the progress with the quest of
    'index' done as well."""
    names = {*self.done, QUESTS[index].name}
    return Progress(''.join('%s\n' % name for name in names))

  def save(self, path: str) -> None:
    """The 'save' method writes the progress to the file at 'path',
    making its folder if there is none."""
    target = Path(path)
    target.parent.mkdir(0o755, True, True)
    target.write_text(str(self))

  @staticmethod
  def load(path: str) -> Progress:
    """The 'load' method returns the progress written to the file at
    'path', or none if it cannot be read."""
    try:
      return Progress(Path(path).read_text())
    except (OSError, ValueError):
      return Progress()
