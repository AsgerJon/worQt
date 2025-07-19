"""
breh
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import overload

from PySide6.QtCore import Qt

KeyboardModifier = Qt.KeyboardModifier
Key = Qt.Key
from PySide6.QtGui import QAction

from moreworktoy.dispatch import Dispatcher


class AbstractAction(QAction):
  setShortcut: Dispatcher
  setIcon: Dispatcher

  @overload
  def setShortcut(self, KeyMod, KeyNum) -> None: ...

  @overload
  def setShortcut(self, KeyNum, KeyMod) -> None: ...

  @overload
  def setShortcut(self, str) -> None: ...

  @overload
  def setShortcut(self, Shortcut) -> None: ...

  @overload
  def setShortcut(self, QKeyCombination) -> None: ...

  @overload
  def setShortcut(self, Key, KeyCombination) -> None: ...

  @overload
  def setShortcut(self, KeyCombination, Key) -> None: ...

  @overload
  def setIcon(self, str) -> None: ...
