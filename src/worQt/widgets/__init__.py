"""
The 'worQt.widgets' package provides the generic, reusable custom widgets:
the fusion bases and the type-specific value editors with the VLC-style
settings dialog.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._base_widget import BaseWidget
from ._container import Container
from ._value_edits import (
  StringValueEdit,
  BoolValueEdit,
  NumberValueEdit,
  valueEditor,
)
from ._settings_dialog import SettingsDialog

__all__ = (
  'BaseWidget',
  'Container',
  'StringValueEdit',
  'BoolValueEdit',
  'NumberValueEdit',
  'valueEditor',
  'SettingsDialog',
)
