"""
SaveAction provides a subclass of QAction for the 'Save' action
commonly found in 'File' menus of applications.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from .. import AbstractAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class SaveAction(AbstractAction):
  """
  SaveAction provides a subclass of QAction for the 'Save' action
  commonly found in 'File' menus of applications.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Save')
    self.setIcon('document-save')
    self.setShortcut('Ctrl+S')
