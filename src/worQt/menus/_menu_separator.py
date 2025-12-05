"""
MenuSeparator subclasses QAction and provides a simple separator in menus.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MenuSeparator(QAction):
  """
  MenuSeparator subclasses QAction and provides a simple separator in menus.
  """

  def __init__(self, *__, **_) -> None:
    super().__init__(*__, **_)
    self.setSeparator(True)
