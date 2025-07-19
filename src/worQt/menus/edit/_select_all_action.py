"""
SelectAllAction provides a subclass of QAction for the 'Select All' action
commonly found in 'Edit' menus of applications.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from .. import AbstractAction

from typing import TYPE_CHECKING

from ...nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class SelectAllAction(AbstractAction):
  """SelectAllAction provides a subclass of QAction for the 'Select All'
  action
  commonly found in 'Edit' menus of applications."""

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Select All')
    self.setIcon('edit-select-all')
    self.setShortcut(KeyNum.KEY_A, KeyMod.CTRL)
    self.setToolTip('Select all items')
    self.setStatusTip('Select all items in the current context')
