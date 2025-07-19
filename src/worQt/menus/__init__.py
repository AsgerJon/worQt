"""
The 'worQt.windows.menus' provides classes and functions related to the
menus in the main application window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._action_box import ActionBox
from ._menu_box import MenuBox
from ._abstract_action import AbstractAction
from ._abstract_menu import AbstractMenu
from . import file, edit, help
from .file import FileMenu
from .edit import EditMenu
from .help import HelpMenu
from ._abstract_menu_bar import AbstractMenuBar
from ._main_menu_bar import MainMenuBar
from ._abstract_status_bar import AbstractStatusBar
from ._main_status_bar import MainStatusBar

__all__ = [
    'ActionBox',
    'MenuBox',
    'AbstractAction',
    'AbstractMenu',
    'file',
    'edit',
    'help',
    'FileMenu',
    'EditMenu',
    'HelpMenu',
    'AbstractMenuBar',
    'MainMenuBar',
    'AbstractStatusBar',
    'MainStatusBar',
]
