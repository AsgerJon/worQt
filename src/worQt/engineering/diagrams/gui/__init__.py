"""
The 'worQt.engineering.diagrams.gui' package draws the section force
diagrams of plane frames, painted with worQt's own widgets:

- DiagramsToolBar: the row of buttons above the frame.
- PaintFrame, FrameView: the frame to scale, its loads, reactions and
  a diagram; its nodes and loads dragged.
- PaintDiagramsPanel, DiagramsPanel: the part selected as numbers and
  buttons, or the frame and its reactions.
- DiagramsWindow: the parts together.
- DiagramsApp: the application, run with
  'python -m worQt.engineering.diagrams'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._diagrams_tool_bar import DiagramsToolBar
from ._paint_frame import PaintFrame
from ._frame_view import FrameView
from ._diagrams_panel import PaintDiagramsPanel, DiagramsPanel
from ._diagrams_window import DiagramsWindow
from ._diagrams_app import DiagramsApp

__all__ = (
  'DiagramsToolBar',
  'PaintFrame',
  'FrameView',
  'PaintDiagramsPanel',
  'DiagramsPanel',
  'DiagramsWindow',
  'DiagramsApp',
)
