"""
Modifier subclasses the 'KeeNum' class from the 'worktoy.keenum' module
and enumerates various keyboard modifiers.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from worktoy.keenum import KeeFlags, KeeFlag

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
  ALT = KeeFlag(Qt.KeyboardModifier.AltModifier)
  CTRL = KeeFlag(Qt.KeyboardModifier.ControlModifier)
  META = KeeFlag(Qt.KeyboardModifier.MetaModifier)
  SHIFT = KeeFlag(Qt.KeyboardModifier.ShiftModifier)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def fromQ(cls, mod: Qt.KeyboardModifier) -> Self:
    index = 0
    if mod & Qt.KeyboardModifier.AltModifier:
      index += 2 ** cls.ALT.index
    if mod & Qt.KeyboardModifier.ControlModifier:
      index += 2 ** cls.CTRL.index
    if mod & Qt.KeyboardModifier.MetaModifier:
      index += 2 ** cls.META.index
    if mod & Qt.KeyboardModifier.ShiftModifier:
      index += 2 ** cls.SHIFT.index
    return cls(index)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getValue(self, ) -> Qt.KeyboardModifier:
    out = Qt.KeyboardModifier.NoModifier
    for high in self.highs:
      out |= high.args[0]
    return out
