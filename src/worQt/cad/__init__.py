"""
The 'cad' package is the self-contained structural-CAD example app. Per the
worQt example pattern, EVERYTHING needed to run it lives here and is exported
from this '__init__'; core worQt (mixin, settings, qtest, the base widgets
and the app/window bases) never imports from 'cad', so the example can later
be stripped in one move.

Two pure subpackages carry the model: 'draw' (the 'dead' drawing primitives)
and 'fea' (the truss analysis). 'CADSettings' is the colour/defaults schema;
'CADWidget' / 'CADWindow' / 'CADApp' are the canvas, window and application;
the tool panels and icons complete the UI.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import draw
from . import fea
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
from ._vertex_editor import VertexEditor
from ._cad_widget import CADWidget
from ._selection_tool import SelectionToolPanel
from ._new_item_tool import NewItemToolPanel
from ._view_tool import ViewToolPanel
from ._cad_settings import CADSettings
from ._cad_window import CADWindow
from ._cad_app import CADApp

__all__ = [
  'draw',
  'fea',
  'navigateIcon',
  'selectIcon',
  'anchorIcon',
  'moduleIcon',
  'memberIcon',
  'supportIcon',
  'loadIcon',
  'dimensionIcon',
  'angleIcon',
  'VertexEditor',
  'CADWidget',
  'SelectionToolPanel',
  'NewItemToolPanel',
  'ViewToolPanel',
  'CADSettings',
  'CADWindow',
  'CADApp',
]
