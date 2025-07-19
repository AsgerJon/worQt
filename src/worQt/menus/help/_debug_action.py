"""
DebugAction provides a non-production action for debugging purposes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Slot

from .. import AbstractAction

from ...nums import KeyNum, KeyMod


class DebugAction(AbstractAction):
  """DebugAction provides a non-production action for debugging purposes."""

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Debug')
    self.setObjectName('menus_help_debug_action')
    self.setIcon('debug')
    self.setShortcut(KeyNum.KEY_F12, KeyMod.NULL)

  @Slot()
  def func(self) -> None:
    pass
