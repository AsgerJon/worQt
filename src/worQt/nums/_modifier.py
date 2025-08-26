"""
Modifier subclasses the 'KeeNum' class from the 'worktoy.keenum' module
and enumerates various keyboard modifiers.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from worktoy.keenum import Kee, KeeFlags

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class KeyMod(KeeFlags):
  """
  Modifier is a subclass of KeeNum that enumerates various keyboard
  modifiers.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Flags
  ALT = Kee[Qt.KeyboardModifier](Qt.KeyboardModifier.AltModifier)
  CTRL = Kee[Qt.KeyboardModifier](Qt.KeyboardModifier.ControlModifier)
  META = Kee[Qt.KeyboardModifier](Qt.KeyboardModifier.MetaModifier)
  SHIFT = Kee[Qt.KeyboardModifier](Qt.KeyboardModifier.ShiftModifier)

  @classmethod
  def fromQ(cls, mod: Qt.KeyboardModifier) -> Self:
    val = 0
    if mod & Qt.KeyboardModifier.AltModifier:
      val |= cls.ALT
    if mod & Qt.KeyboardModifier.ControlModifier:
      val |= cls.CTRL
    if mod & Qt.KeyboardModifier.MetaModifier:
      val |= cls.META
    if mod & Qt.KeyboardModifier.ShiftModifier:
      val |= cls.SHIFT
    return val
