"""
CircuitsTest and CircuitsWidgetTest are the base classes for the tests
of 'worQt.engineering.circuits': 'CircuitsTest' subclasses 'BaseTest'
for the model, which needs no Qt; 'CircuitsWidgetTest' subclasses
'WidgetTest' for the widgets.

'loop' makes a circuit of parts round the four corners of a square,
N1 at the bottom left, then up, right and down; 'rlc' a source, a
resistor, a coil and a capacitor round it, the hand's own series
circuit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering.circuits import Capacitor, Circuit, Coil, Node
from worQt.engineering.circuits import Resistor, Source
from worQt.qtest import WidgetTest

SQUARE = (Node(0.0, 0.0), Node(0.0, 2.0), Node(2.0, 2.0), Node(2.0, 0.0))


def loop(*parts) -> Circuit:
  """The 'loop' function returns 'parts' on the four corners of a
  square: N1 at the bottom left, N2 above it, N3 at the top right, N4
  under it."""
  return Circuit(SQUARE, parts)


def rlc(voltage: float, resistance: float, inductance: float,
        capacitance: float) -> Circuit:
  """The 'rlc' function returns a steady source of 'voltage', its plus
  pole at N2, driving a resistor, a coil and a capacitor in series
  round the square: the capacitor E1's minus pole to N4."""
  return loop(Source(1, 0, voltage, 0.0, 0.0),
              Resistor(1, 2, resistance), Coil(2, 3, inductance),
              Capacitor(3, 0, capacitance))


class CircuitsTest(BaseTest):
  """Base class for the tests of the circuits' model."""


class CircuitsWidgetTest(WidgetTest):
  """Base class for the tests of the circuits' widgets."""
