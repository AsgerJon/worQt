"""
KeyboardShortcuts enumerates common keyboard shortcuts. It provides a
parallel to the FreeDesktopIcon enumeration for keyboard shortcuts.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QKeySequence
from icecream import ic

from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class KeyboardShortcuts(KeeNum):
  """
  KeyboardShortcuts enumerates common keyboard shortcuts.
  """

  NEW = Kee[str]('Ctrl+N')
  OPEN = Kee[str]('Ctrl+O')
  SAVE = Kee[str]('Ctrl+S')
  PRINT = Kee[str]('Ctrl+P')
  QUIT = Kee[str]('ALT+F4')
  UNDO = Kee[str]('Ctrl+Z')
  REDO = Kee[str]('Ctrl+Y')
  CUT = Kee[str]('Ctrl+X')
  COPY = Kee[str]('Ctrl+C')
  PASTE = Kee[str]('Ctrl+V')
  SELECT_ALL = Kee[str]('Ctrl+A')
  ABOUT = Kee[str]('F12')
  HELP = Kee[str]('F1')
  FALLBACK = Kee[str]('')

  Q = Field()

  @Q.GET
  def _getQ(self, ) -> QKeySequence:
    if self.value:
      fmt = QKeySequence.SequenceFormat.PortableText
      return QKeySequence.fromString(self.value, fmt)
    return QKeySequence()

  @classmethod
  def findShortcut(cls, iconName: str) -> Self:
    for member in cls:
      if iconName.lower() in member.value.lower():
        return member
    for member in cls:
      if member.name.lower() in iconName.lower():
        return member
    return cls.FALLBACK

  @classmethod
  def resolveMember(cls, identifier: str) -> Self:
    """
    This method resolves a member of the enumeration based on a given
    identifier. The identifier can be either the name or the value of the
    member. The search is case-insensitive and ignores leading and trailing
    whitespace. If no exact match is found, it attempts to find a partial
    match. If still no match is found, it returns the FALLBACK member.
    """
    ident = str.lower(str.strip(identifier, ))
    for member in cls:
      name = str.lower(member.name)
      value = str.lower(member.value)
      if ident in (name, value,):
        return member
    else:
      for member in cls:
        name = str.lower(member.name)
        value = str.lower(member.value)
        if ident in name or ident in value:
          return member
    return cls.FALLBACK

  @classmethod
  def validateKeySequence(cls, keySeq: str) -> bool:
    """
    This method validates if a given string is a valid key sequence.
    """
    fmt = QKeySequence.SequenceFormat.PortableText
    ks = QKeySequence.fromString(keySeq, fmt)
    return False if ks.isEmpty() else True
