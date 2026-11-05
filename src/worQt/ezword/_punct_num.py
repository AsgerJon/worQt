"""
PunctNum enumerates punctuation characters.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.keenum import Kee, KeeNum

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class PunctNum(KeeNum):
  """
  PunctNum enumerates the punctuation marks that separate sentences: a
  paragraph splits its text into sentences behind any of them. The
  comma is no punctuation here, since it separates the clauses within a
  sentence. Punctuation decides case: 'capitalize' tells whether the
  sentence after a mark starts with a capital.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Enumerations
  PERIOD: Kee[str] = Kee[str]('.')
  QUESTION: Kee[str] = Kee[str]('?')
  EXCLAMATION: Kee[str] = Kee[str]('!')
  SEMICOLON: Kee[str] = Kee[str](';')
  COLON: Kee[str] = Kee[str](':')
  ELLIPSIS: Kee[str] = Kee[str]('...')

  #  Virtual Variables
  capitalize: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @capitalize.GET
  def _getCapitalize(self, ) -> bool:
    """
    The 'capitalize' getter returns False for the colon, the semicolon
    and the ellipsis, after which the next sentence continues in lower
    case, and True for every other mark.
    """
    cls = type(self)
    lower = (cls.COLON, cls.SEMICOLON, cls.ELLIPSIS)
    return False if self in lower else True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def ending(cls, text: str) -> Optional[PunctNum]:
    """
    The 'ending' method returns the mark 'text' ends with, or 'None'.
    Where several match, the longest wins, so '...' ends with the
    ellipsis rather than a period.
    """
    found = None
    for mark in cls:
      if str.endswith(text, mark.value):
        if found is None or len(mark.value) > len(found.value):
          found = mark
    return found
