"""
The 'worQt.windows.menus.edit' package provides the actions and the menu
class for the common 'Edit' menu in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._select_all_action import SelectAllAction
from ._copy_action import CopyAction
from ._cut_action import CutAction
from ._paste_action import PasteAction
from ._edit_menu import EditMenu

__all__ = [
    'SelectAllAction',
    'CopyAction',
    'CutAction',
    'PasteAction',
    'EditMenu',
]
