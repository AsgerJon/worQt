"""
The 'worQt.engineering.gui' package shows the engineering model, painted
with worQt's own widgets and paint operations, and edits it the way any
drawing program does.

- GripNum: what can be selected or taken hold of on a disk.
- DiskGrip: what is selected or held: the kind, the part, the edge.
- PaintDisk: the paint operation drawing a disk, its supports, loads,
  dimensions and handles.
- DiskWidget: the drawing: a disk to scale, edited with the mouse.
- NumberField: a form field holding one number with its unit.
- ToolButton: a button saying what it does.
- Slider: a slider saying what it sets and how much.
- QuantitySlider: a slider setting a quantity, shown in its unit.
- CheckBox: a box ticked or not, with what it means beside it.
- crackColor and the rest of '_crack_colors': cracks coloured by their
  size on a log scale from a micrometre to a millimetre, and the scale.
- TestStatus: the strip along a window's bottom saying what is going
  on in a test, a bar moving while work goes on.
- niceAbove: a number rounded up to one an axis is ticked at; niceSpan:
  an axis's ends and step either side of nought.
- PaintTimeCurve, TimeCurve: a few things against time, the last
  stretch of them.
- DiskInspector: the panel showing what is selected as numbers.
- DiskToolBar: the row of buttons above the drawing.
- DiskWindow: the buttons, the drawing and the panel together.
- DiskApp: the application, run with 'python -m worQt.engineering'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._grip_num import GripNum
from ._disk_grip import DiskGrip
from ._paint_disk import PaintDisk
from ._disk_widget import DiskWidget
from ._number_field import NumberField
from ._tool_button import ToolButton
from ._slider import Slider
from ._quantity_slider import QuantitySlider
from ._check_box import CheckBox
from ._crack_colors import crackColor, crackShare, crackTicks
from ._crack_colors import crackLevel, levelColor, paintCrackScale
from ._crack_colors import CRACK_LEAST, CRACK_MOST, CRACK_LEVELS
from ._test_status import TestStatus, PaintTestStatus
from ._nice_above import niceAbove, niceSpan
from ._time_curve import PaintTimeCurve, TimeCurve
from ._disk_inspector import DiskInspector
from ._disk_tool_bar import DiskToolBar
from ._disk_window import DiskWindow
from ._disk_app import DiskApp

__all__ = (
  'GripNum',
  'DiskGrip',
  'PaintDisk',
  'DiskWidget',
  'NumberField',
  'ToolButton',
  'Slider',
  'QuantitySlider',
  'CheckBox',
  'crackColor',
  'crackShare',
  'crackTicks',
  'crackLevel',
  'levelColor',
  'paintCrackScale',
  'CRACK_LEAST',
  'CRACK_MOST',
  'CRACK_LEVELS',
  'TestStatus',
  'PaintTestStatus',
  'niceAbove',
  'niceSpan',
  'PaintTimeCurve',
  'TimeCurve',
  'DiskInspector',
  'DiskToolBar',
  'DiskWindow',
  'DiskApp',
)
