"""
PageWidget subclasses 'Vidget' and is the page EZWord writes on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.waitaminute import TypeException

from ...utils.geom import InSets
from ...vidget import Vidget
from .. import Char, PunctNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class PageWidget(Vidget):
  """
  PageWidget subclasses 'Vidget' and is the page EZWord writes on: Vi,
  on a page. It takes only what the EZWord format holds - letters, the
  space, the comma, the line break and the 'PunctNum' marks - so no key
  puts anything else in the text. Letters have no case of their own; the
  page shows each one as the punctuation decides: a capital at the start
  of a paragraph and after a mark whose 'capitalize' is True, lower case
  everywhere else.

  Each page is one file open in EZWord, in a tab of its own: its
  'filePath' is the file it was opened from or saved to, or 'None' for a
  page never saved, and its 'title' is that file's name.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(8, 8, 8, 8)
  __fallback_borders_dims__ = InSets(1, 1, 1, 1)
  __fallback_paddings_dims__ = InSets(16, 16, 16, 16)
  __untitled_name__ = 'untitled'

  #  Private Variables
  __page_file__: Optional[str] = None

  #  Public Variables
  filePath: Field[str] = Field()

  #  Virtual Variables
  title: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @filePath.GET
  def _getFilePath(self, ) -> Optional[str]:
    """The 'filePath' getter returns the page's file, or 'None' for a
    page never saved."""
    return self.__page_file__

  @filePath.SET
  def _setFilePath(self, path: Optional[str]) -> None:
    if path is not None and not isinstance(path, str):
      raise TypeException('filePath', path, str)
    self.__page_file__ = None if path is None else os.path.abspath(path)

  @title.GET
  def _getTitle(self, ) -> str:
    """The 'title' getter returns the name of the page's file."""
    if self.filePath is None:
      return self.__untitled_name__
    return os.path.basename(self.filePath)

  def _getShownText(self, ) -> str:
    """
    The page shows its text cased by the punctuation, letter for letter.
    A run of marks decides by its last mark, and a blank line starts a
    new paragraph, which starts with a capital.
    """
    marks = self._markChars()
    out, capitalize, run, blankLine = [], True, '', True
    for char in self.text:
      if char in marks:
        run, blankLine = run + char, False
        out.append(char)
        continue
      if run:
        capitalize, run = PunctNum.ending(run).capitalize, ''
      if char == '\n':
        capitalize = True if blankLine else capitalize
        blankLine = True
      elif char != ' ':
        blankLine = False
      if self._isLetter(char):
        char = str.upper(char) if capitalize else str.lower(char)
        capitalize = False
      out.append(char)
    return ''.join(out)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _markChars() -> str:
    return ''.join(mark.value for mark in PunctNum)

  @staticmethod
  def _isLetter(char: str) -> bool:
    return True if str.upper(char) in [c.value for c in Char] else False

  def matchable(self, text: str) -> str:
    """A search on the page ignores case, which the page's letters do
    not have."""
    return str.lower(text)

  def accepts(self, char: str) -> bool:
    """
    The 'accepts' method tells whether the page can hold 'char': a
    letter, the space, the comma, the line break or a punctuation mark.
    """
    if len(char) != 1:
      return False
    if char in ' ,\n' or char in self._markChars():
      return True
    return self._isLetter(char)
