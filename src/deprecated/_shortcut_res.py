"""ShortcutRes enumerates common keyboard shortcuts."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
import json

from PySide6.QtGui import QKeySequence
from worktoy.keenum import auto

from worQt import getResourcePath, Shiboken
from worQt.resources import ResNum

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class ShortcutRes(ResNum):
  """ShortcutRes enumerates common keyboard shortcuts."""

  def getResPath(self) -> str:
    """Get the resource string for the shortcut."""
    return getResourcePath()

  def getResType(self) -> Shiboken:
    """Get the resource type for the shortcut."""
    return QKeySequence

  def createResType(self) -> QKeySequence:
    """Create the resource type for the shortcut."""
    resPath = self.getResPath()
    fileName = 'shortcuts.json'
    fid = os.path.join(resPath, fileName)
    with open(fid, 'r') as file:
      data = json.load(file)
    stringCut = data.get(self.key, '')
    if stringCut:
      return QKeySequence(stringCut)
    return self.fallbackResType()

  def fallbackResType(self) -> QKeySequence:
    """Return the fallback resource type for the shortcut."""
    return QKeySequence()

  NEW = auto()
  OPEN = auto()
  SAVE = auto()
  SAVE_AS = auto()
  EXIT = auto()
  PRINT = auto()
  UNDO = auto()
  REDO = auto()
  CUT = auto()
  COPY = auto()
  PASTE = auto()
  SELECT_ALL = auto()
  ABOUT_QT = auto()
  ABOUT_PYTHON = auto()
  HELP = auto()
  SETTINGS = auto()
