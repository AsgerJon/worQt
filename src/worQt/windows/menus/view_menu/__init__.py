"""
The 'worQt.windows.menus.view_menu' package provides the view menu actions
for the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._full_screen_action import FullScreenAction
from ._zoom_in_action import ZoomInAction
from ._zoom_out_action import ZoomOutAction
from ._zoom_reset_action import ZoomResetAction
from ._view import View

__all__ = (
  'FullScreenAction',
  'ZoomInAction',
  'ZoomOutAction',
  'ZoomResetAction',
  'View',
)
