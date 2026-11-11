"""
The 'worQt.engineering.circuits.gui' package shows electric circuits
running, painted with worQt's own widgets:

- SPEEDS, PaintSpeedStops, SpeedSlider, speedText, speedWords,
  nearestStop: the slider setting how fast the circuit runs, stop by
  stop, and the speeds said.
- CircuitsToolBar: the row of buttons above the circuit.
- PaintCircuit, CircuitView: the circuit on its grid, its parts as
  their symbols, coloured by voltage, the current as dots; its nodes
  dragged and joined.
- PaintProgramEditor, ProgramEditor, said, operandText: a ROM's
  program, a word a row, each written from a menu; a word and its
  operand as they are written.
- PaintCircuitsPanel, CircuitsPanel: the part selected as numbers,
  buttons and what it reads, or the circuit and its energy.
- CircuitsWindow: the parts together, with the voltages and currents
  against time.
- CircuitsApp: the application, run with
  'python -m worQt.engineering.circuits'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._speed_slider import SPEEDS, PaintSpeedStops, SpeedSlider
from ._speed_slider import nearestStop, speedText, speedWords
from ._circuits_tool_bar import CircuitsToolBar
from ._paint_circuit import PaintCircuit
from ._circuit_view import CircuitView
from ._program_editor import PaintProgramEditor, ProgramEditor, said
from ._program_editor import operandText
from ._circuits_panel import PaintCircuitsPanel, CircuitsPanel
from ._circuits_window import CircuitsWindow
from ._circuits_app import CircuitsApp

__all__ = (
  'SPEEDS',
  'PaintSpeedStops',
  'SpeedSlider',
  'nearestStop',
  'speedText',
  'speedWords',
  'CircuitsToolBar',
  'PaintCircuit',
  'CircuitView',
  'PaintProgramEditor',
  'ProgramEditor',
  'said',
  'operandText',
  'PaintCircuitsPanel',
  'CircuitsPanel',
  'CircuitsWindow',
  'CircuitsApp',
)
