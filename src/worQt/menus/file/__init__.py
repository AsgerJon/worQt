"""The 'worQt.windows.menus.file' package provides the actions and the
menu object for the common 'File' menu in the worQt framework."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._new_action import NewAction
from ._open_action import OpenAction
from ._save_action import SaveAction
from ._exit_action import ExitAction
from ._file_menu import FileMenu

__all__ = [
    'NewAction',
    'OpenAction',
    'SaveAction',
    'ExitAction',
    'FileMenu',
]
