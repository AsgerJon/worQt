"""
MenuSeparator subclasses 'AbstractAction' and provides a menu separator in
the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction

from . import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MenuSeparator(AbstractAction):
  """
  MenuSeparator subclasses 'AbstractAction' and provides a menu separator in
  the main window.
  """

  def __init__(self, *args, **kwargs) -> None:
    parent = self._resolveParent(*args)
    super().__init__(parent)
    QAction.setSeparator(self, True)
