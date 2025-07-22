"""
OpenAction provides a QAction subclass for the 'Open' action commonly found
in 'File' menus of applications.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from .. import AbstractAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class OpenAction(AbstractAction):
  """
  OpenAction provides a QAction subclass for the 'Open' action commonly found
  in 'File' menus of applications.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('Open')
    self.setIcon('document-open')
    self.setShortcut('Ctrl+O')
