"""
The 'worQt.settings' module contains the application settings.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._settings_field import SettingsField
from ._abstract_settings import AbstractSettings
from ._mouse_click_settings import MouseClickSettings
from ._window_settings import WindowSettings

___all__ = [
    'SettingsField',
    'AbstractSettings',
    'MouseClickSettings',
    'WindowSettings',
]
