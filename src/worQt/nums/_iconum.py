"""
IcoNum enumerates the icons used in worQt.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QIcon
from worktoy.keenum import KeeNum, Kee

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Self, Optional


class IcoNum(KeeNum):
  """
  IcoNum enumerates the icons used in worQt.
  """
  NEW = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentNew)
  OPEN = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentOpen)
  SAVE = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentSave)
  SAVE_AS = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentSaveAs)
  PRINT = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentPrint)
  EXIT = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.ApplicationExit)
  UNDO = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditUndo)
  REDO = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditRedo)
  CUT = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditCut)
  COPY = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditCopy)
  PASTE = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditPaste)
  DELETE = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditDelete)
  SELECT_ALL = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditSelectAll)
  FIND = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.EditFind)
  ABOUT = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.HelpAbout)
  ABOUT_QT = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.HelpAbout)
  HELP = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.HelpAbout)
  PROPERTIES = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentProperties)
  SETTINGS = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.DocumentProperties)
  FULLSCREEN = Kee[QIcon.ThemeIcon](QIcon.ThemeIcon.ViewFullscreen)
