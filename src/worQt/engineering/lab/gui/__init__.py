"""
The 'worQt.engineering.lab.gui' package is the beam lab, painted with
worQt's own widgets:

- LabToolBar: the row of buttons above the beam.
- PaintBeam, BeamView: the beam on its rig as the lab sees it; the rig's
  parts dragged along the beam.
- PaintLabCurve, LabCurve: the total force against the displacements
  measured, as the test runs.
- PaintControlCurve, ControlCurve: the control's command and feedback
  against time.
- PaintBeamPanel, BeamPanel: the beam's numbers.
- PaintControlPanel, ControlPanel: the control loop and the part of
  the rig selected.
- LabWindow: the lab, the parts together.
- LabApp: the application, run with 'python -m worQt.engineering.lab'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._lab_tool_bar import LabToolBar
from ._paint_beam import PaintBeam
from ._beam_view import BeamView
from ._paint_lab_curve import PaintLabCurve
from ._lab_curve import LabCurve
from ._control_curve import PaintControlCurve, ControlCurve
from ._beam_panel import PaintBeamPanel, BeamPanel
from ._control_panel import PaintControlPanel, ControlPanel
from ._lab_window import LabWindow
from ._lab_app import LabApp

__all__ = (
  'LabToolBar',
  'PaintBeam',
  'BeamView',
  'PaintLabCurve',
  'LabCurve',
  'PaintControlCurve',
  'ControlCurve',
  'PaintBeamPanel',
  'BeamPanel',
  'PaintControlPanel',
  'ControlPanel',
  'LabWindow',
  'LabApp',
)
