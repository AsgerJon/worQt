"""
The 'worQt.widgets' package provides custom widgets.
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
from ._cad_widget import CADWidget
from ._vertex_editor import VertexEditor
from ._selection_tool import SelectionToolPanel
from ._new_item_tool import NewItemToolPanel
from ._view_tool import ViewToolPanel
from ._tool_icons import (
  navigateIcon,
  selectIcon,
  anchorIcon,
  moduleIcon,
  memberIcon,
  supportIcon,
  loadIcon,
  dimensionIcon,
  angleIcon,
)

__all__ = (
  'BaseWidget',
  'Container',
  'StringValueEdit',
  'BoolValueEdit',
  'NumberValueEdit',
  'valueEditor',
  'SettingsDialog',
  'CADWidget',
  'VertexEditor',
  'SelectionToolPanel',
  'NewItemToolPanel',
  'ViewToolPanel',
  'navigateIcon',
  'selectIcon',
  'anchorIcon',
  'moduleIcon',
  'memberIcon',
  'supportIcon',
  'loadIcon',
  'dimensionIcon',
  'angleIcon',
)
