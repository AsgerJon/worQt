"""MenuBar provides the menu bar for the main window."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QMenuBar
from worktoy.attr import AttriBox
from worktoy.static import THIS

from . import FileMenu, EditMenu, HelpMenu

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class MenuBar(QMenuBar):
  """MenuBar provides the menu bar for the main window."""

  file = AttriBox[FileMenu](THIS)
  edit = AttriBox[EditMenu](THIS)
  help = AttriBox[HelpMenu](THIS)

  def initUi(self) -> None:
    """Initialize the UI."""
    self.file.initUi()
    self.addMenu(self.file)
    self.edit.initUi()
    self.addMenu(self.edit)
    self.help.initUi()
    self.addMenu(self.help)
