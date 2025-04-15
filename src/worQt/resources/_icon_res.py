"""IconRes enumerates the icon images. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os

from PySide6.QtGui import QIcon, QPixmap
from worktoy.keenum import auto
from worktoy.text import monoSpace

from worQt import getIconPath
from worQt.resources import ResNum

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from .. import Shiboken


class IconRes(ResNum):
  """IconRes enumerates the icon images. """

  __fallback_file__ = 'risitas'

  @classmethod
  def getResPath(cls) -> str:
    """Return the resource path for the icon."""
    return getIconPath()

  @classmethod
  def getResType(cls) -> Shiboken:
    """Return the resource type for the icon."""
    return QIcon

  def createResType(self, ) -> QIcon:
    """Create the resource type for the icon."""
    resPath = self.getResPath()
    for item in os.listdir(resPath):
      if item.startswith(self.key):
        pix = QPixmap(os.path.join(resPath, item))
        return QIcon(pix)
    return self.fallbackResType()

  @classmethod
  def fallbackResType(cls) -> QIcon:
    """Return the fallback resource type for the icon."""
    resPath = cls.getResPath()
    for item in os.listdir(resPath):
      if item.startswith(cls.__fallback_file__):
        pix = QPixmap(os.path.join(resPath, item))
        return QIcon(pix)
    raise FileNotFoundError

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
