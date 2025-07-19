"""
Shortcut encapsulates a keyboard shortcut as a descriptor in the worQt
framework. Instances of this class return a `QKeySequence` object
when accessed (__get__(...) -> QKeySequence).
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QKeyCombination, Qt
from PySide6.QtGui import QKeySequence
from worktoy.desc import Field, LabelBox
from worktoy.mcls import BaseObject

from moreworktoy.dispatch import overload
from ..nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  pass


class Shortcut(BaseObject):
  """
  Shortcut encapsulates a keyboard shortcut as a descriptor in the worQt
  framework. Instances of this class return a `QKeySequence` object
  when accessed (__get__(...) -> QKeySequence).
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  key = LabelBox[KeyNum]()
  mods = LabelBox[KeyMod]()
  Q = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @Q.GET
  def _getQ(self) -> QKeySequence:
    return QKeySequence(self.key, self.mods)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QKeyCombination)
  def __init__(self, keyCombination: QKeyCombination) -> None:
    self.key = keyCombination.key()
    self.mods = keyCombination.keyboardModifiers()

  @overload(str)
  def __init__(self, keyStr: str) -> None:
    keySequence = QKeySequence.fromString(keyStr)
    keyCombination = QKeyCombination.fromCombined(keySequence[0], )

  @overload.flex(KeyNum, KeyMod)
  def __init__(self, *args) -> None:
    for arg in args:
      if isinstance(arg, KeyNum):
        self.key = arg
        continue
      if isinstance(arg, KeyMod):
        self.mods = arg
        continue

  @overload(KeyNum)
  def __init__(self, key: KeyNum) -> None:
    self.key = key
    self.mods = KeyMod.NULL

  @overload(Qt.Key)
  def __init__(self, key: Qt.Key) -> None:
    self.key = KeyNum.fromValue(key)
    self.mods = KeyMod.NULL
