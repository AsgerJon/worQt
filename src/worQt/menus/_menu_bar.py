"""
MainMenuBar subclasses QMenuBar to provide the main menu bar for the
application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QMenuBar, QMainWindow
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from . import EditMenu, HelpMenu, FileMenu


class MainMenuBar(QMenuBar):
  """
  MainMenuBar subclasses QMenuBar to provide the main menu bar for the
  application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  file = AttriBox[FileMenu](THIS)
  edit = AttriBox[EditMenu](THIS)
  help = AttriBox[HelpMenu](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, main: QMainWindow) -> None:
    QMenuBar.__init__(self, main)
    self.addMenu(self.file)
    self.addMenu(self.edit)
    self.addMenu(self.help)
