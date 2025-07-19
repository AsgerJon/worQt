"""
MainMenuBar provides the main menu bar for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core.sentinels import THIS

from . import AbstractMenuBar, MenuBox, FileMenu, EditMenu, HelpMenu

if TYPE_CHECKING:  # pragma: no cover
  pass


class MainMenuBar(AbstractMenuBar):
  """
  MainMenuBar provides the main menu bar for the application.
  It is a subclass of AbstractMenuBar and sets up the main menu structure.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables

  #  Public Variables
  file = MenuBox[FileMenu](THIS)
  edit = MenuBox[EditMenu](THIS)
  help = MenuBox[HelpMenu](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    """
    Subclasses must implement this method. Menus should be defined as
    LabelBox descriptors in the class body. This method should then add
    each menu using `self.addMenu(self.menuName)`. This method runs before
    the 'initLogic' method defined below.
    """
    self.addMenu(self.file, )
    self.addMenu(self.edit, )
    self.addMenu(self.help, )

  def initLogic(self) -> None:
    """
    Subclasses may implement this method to connect any particular menu
    to a specific logic. By default, menus are already added by the
    'initUi' defined above making them available externally.
    """
