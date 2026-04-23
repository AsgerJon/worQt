"""
MainMenuBar subclasses 'WMenuBar' and provides the menubar of the main
application window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import QMenu, QMenuBar
from icecream import ic
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.utilities import textFmt

from . import WMenuBar, FileMenu, EditMenu, HelpMenu, DebugMenu, WMenu

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  MenuBox: TypeAlias = Union[QMenu, AttriBox]
  DebugBox: TypeAlias = Union[DebugMenu, AttriBox]
  FileBox: TypeAlias = Union[FileMenu, AttriBox]
  EditBox: TypeAlias = Union[EditMenu, AttriBox]
  HelpBox: TypeAlias = Union[HelpMenu, AttriBox]
  ActionMenu: TypeAlias = Union[QMenu, QAction]


class MainMenuBar(WMenuBar):
  """
  MainMenuBar subclasses 'WMenuBar' and provides the menubar of the main
  application window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  file: FileBox = AttriBox[FileMenu](THIS)
  edit: EditBox = AttriBox[EditMenu](THIS)
  help_: HelpBox = AttriBox[HelpMenu](THIS)
  debug: DebugBox = AttriBox[DebugMenu](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initialize the user interface of the menubar by adding the menus.
    """
    super().initUI()
    self.addMenu(self.file)
    self.addMenu(self.edit)
    self.addMenu(self.help_)
    self.addMenu(self.debug)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addMenu(self, *args, ) -> ActionMenu:
    menu, *_ = (*args, None)
    if isinstance(menu, WMenu):
      menu.initUI()
      return WMenuBar.addMenu(self, menu)
    return WMenuBar.addMenu(self, *args, )
