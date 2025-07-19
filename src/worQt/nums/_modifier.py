"""
Modifier subclasses the 'KeeNum' class from the 'worktoy.keenum' module
and enumerates various keyboard modifiers.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.keenum import KeeNum, Kee

from worktoy.keenum import KeeFlags


class KeyMod(KeeFlags):
  """
  Modifier is a subclass of KeeNum that enumerates various keyboard
  modifiers.
  """
  ALT = Kee[Qt.Modifier](Qt.Modifier.ALT)
  CTRL = Kee[Qt.Modifier](Qt.Modifier.CTRL)
  META = Kee[Qt.Modifier](Qt.Modifier.META)
  SHIFT = Kee[Qt.Modifier](Qt.Modifier.SHIFT)
