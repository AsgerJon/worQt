"""
MenuSeparator subclasses 'QAction' and is restricted to be a separator in
menus.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QAction


class MenuSeparator(QAction):
  """
  MenuSeparator subclasses 'QAction' and is restricted to be a separator in
  menus.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setSeparator(True)
