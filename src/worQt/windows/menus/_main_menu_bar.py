"""
MainMenuBar subclasses 'AbstractMenuBar' and provides the standard menu bar
for a main window: File, Edit, View and Help. The menus are declared as
'MenuBox' fields, which register their type on the bar; 'initUI' then builds
and assembles them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractMenuBar, MenuBox
from .file_menu import File
from .edit_menu import Edit
from .view_menu import View
from .help_menu import Help

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class MainMenuBar(AbstractMenuBar):
  """
  MainMenuBar subclasses 'AbstractMenuBar' and provides the standard menu
  bar for a main window: File, Edit, View and Help.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Menus
  fileMenu = MenuBox[File]()
  editMenu = MenuBox[Edit]()
  viewMenu = MenuBox[View]()
  helpMenu = MenuBox[Help]()
