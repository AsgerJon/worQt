"""
The 'worQt.windows.menus' provides classes and functions related to the
menus in the main application window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._w_action import WAction
from ._menu_separator import MenuSeparator
from ._action_box import ActionBox
from ._file_menu import FileMenu
from ._edit_menu import EditMenu
from ._help_menu import HelpMenu
from ._menu_bar import MainMenuBar

__all__ = [
    'WAction',
    'MenuSeparator',
    'ActionBox',
    'FileMenu',
    'EditMenu',
    'HelpMenu',
    'MainMenuBar',
]
