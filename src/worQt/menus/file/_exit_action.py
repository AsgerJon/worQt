"""
ExitAction provides a subclass of QAction for the 'Exit' action
commonly found in 'File' menus of applications.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QAction

from .. import AbstractAction

from typing import TYPE_CHECKING

from ...nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class ExitAction(AbstractAction):
  """ExitAction provides a subclass of QAction for the 'Exit' action
  commonly found in 'File' menus of applications."""

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Exit')
    self.setIcon('application-exit')
    self.setShortcut(KeyNum.KEY_F4, KeyMod.ALT)
    self.setMenuRole(QAction.MenuRole.QuitRole)
