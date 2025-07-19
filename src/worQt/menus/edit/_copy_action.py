"""
CopyAction class for the edit menu in a Qt application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from .. import AbstractAction

from ...nums import KeyNum, KeyMod

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class CopyAction(AbstractAction):
  """
  CopyAction provides a QAction subclass for the 'Copy' action commonly found
  in 'Edit' menus of applications.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Copy')
    self.setIcon('edit-copy')
    self.setShortcut(KeyNum.KEY_C, KeyMod.CTRL)
