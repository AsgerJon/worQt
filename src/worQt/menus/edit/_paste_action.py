"""
PasteAction provides the Paste action for the Edit menu in the main window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from .. import AbstractAction
from typing import TYPE_CHECKING

from ...nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class PasteAction(AbstractAction):
  """
  PasteAction provides a subclass of QAction for the 'Paste' action
  commonly found in 'Edit' menus of applications.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Paste')
    self.setIcon('edit-paste')
    self.setShortcut(KeyNum.KEY_F4, KeyMod.CTRL)
