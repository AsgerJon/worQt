"""
FreeDesktopIcon provides easy access to the most common FreeDesktop.org
icons.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon
from worktoy.desc import Field
from worktoy.keenum import KeeNum, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union, Self

  StrField: TypeAlias = Union[Field, str]
  IconField: TypeAlias = Union[Field, QIcon]


class FreeDesktopIcon(KeeNum):
  """
  FreeDesktopIcon provides easy access to the most common FreeDesktop.org
  icons.
  """

  NEW = Kee[str]('document-new')
  OPEN = Kee[str]('document-open')
  SAVE = Kee[str]('document-save')
  PRINT = Kee[str]('document-print')
  QUIT = Kee[str]('application-exit')
  UNDO = Kee[str]('edit-undo')
  REDO = Kee[str]('edit-redo')
  CUT = Kee[str]('edit-cut')
  COPY = Kee[str]('edit-copy')
  PASTE = Kee[str]('edit-paste')
  DELETE = Kee[str]('edit-delete')
  SELECT_ALL = Kee[str]('edit-select-all')
  PREFERENCES = Kee[str]('preferences-system')
  ABOUT = Kee[str]('help-about')
  HELP = Kee[str]('help-contents')
  FALLBACK = Kee[str]('application-x-generic')
  NULL = Kee[str]('')

  Q: IconField = Field()

  @Q.GET
  def _getQ(self, ) -> QIcon:
    if not self.value:
      return QIcon()
    return QIcon.fromTheme(self.value)

  @classmethod
  def findIcon(cls, iconName: str) -> Self:
    for member in cls:
      if iconName.lower() in member.value.lower():
        return member
    name = str.strip(str.replace(iconName, 'Action', ''))
    for member in cls:
      if name.lower() in member.value.lower():
        return member
    return cls.FALLBACK

  @classmethod
  def resolveMember(cls, identifier: str) -> Self:
    ident = str.lower(str.strip(identifier, ))
    for member in cls:
      name = str.lower(member.name)
      value = str.lower(member.value)
      if ident in (name, value,):
        return member
    else:
      for member in cls:
        ident = str.lower(str.strip(identifier, ))
        name = str.lower(member.name)
        value = str.lower(member.value)
        if ident in name or ident in value:
          return member
    return cls.FALLBACK

  @classmethod
  def validateIcon(cls, iconName: str) -> bool:
    return False if cls.findIcon(iconName) is cls.FALLBACK else True
