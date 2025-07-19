"""
NewAction provides the 'New' action commonly found in 'File' menu.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractAction
from ...nums import KeyNum, KeyMod

if TYPE_CHECKING:  # pragma: no cover
  pass


class NewAction(AbstractAction):
  """
  NewAction provides the 'New' action commonly found in 'File' menu.
  """

  def __init__(self, *args, **kwargs) -> None:
    self.setText('New')
    self.setIcon('document-new')
    self.setShortcut(KeyNum.KEY_N, KeyMod.CTRL)
  