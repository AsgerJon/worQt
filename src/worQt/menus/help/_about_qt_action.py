"""
AboutQtAction class for displaying information about the Qt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .. import AbstractAction

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class AboutQtAction(AbstractAction):
  """
  AboutQtAction provides a QAction subclass for displaying information
  about the Qt framework.
  It is typically used in 'Help' menus of applications.
  """

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setText('About Qt')
    self.setIcon('help-about')
    self.triggered.connect(QApplication.aboutQt)
