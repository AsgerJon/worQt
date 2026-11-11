"""
The 'worQt.engineering.springs.gui' package shows masses swinging on
springs in space, painted with worQt's own widgets:

- SpringsToolBar: the row of buttons above the springs.
- PaintScene, SceneView: the system in space, in perspective, turned by
  the mouse; its points dragged, set up, or held by the hand, moving.
- PaintSpringsPanel, SpringsPanel: the part selected as numbers, or the
  system and its modes.
- SpringsWindow: the parts together.
- SpringsApp: the application, run with
  'python -m worQt.engineering.springs'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._springs_tool_bar import SpringsToolBar
from ._paint_scene import PaintScene
from ._scene_view import SceneView
from ._springs_panel import PaintSpringsPanel, SpringsPanel
from ._springs_window import SpringsWindow
from ._springs_app import SpringsApp

__all__ = (
  'SpringsToolBar',
  'PaintScene',
  'SceneView',
  'PaintSpringsPanel',
  'SpringsPanel',
  'SpringsWindow',
  'SpringsApp',
)
