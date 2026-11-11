"""
RunCircuitsWindow covers 'CircuitsApp' and its 'CircuitsWindow': it
opens running the standard circuit; 'Pause', 'Play' and 'Reset'; the
switch closed in the panel lights the lamp and charges the capacitor;
parts are added from a node, between two nodes, or in a wire's place,
and set in the panel; a transistor beside a node or joining three; the
speed buttons slow it and the curves with it; the examples load from
their menu; a short circuit is said.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.engineering.circuits import Ammeter, Circuit, Diode, EXAMPLES
from worQt.engineering.circuits import Node, Resistor, Source
from worQt.engineering.circuits import Transistor, Wire
from worQt.engineering.circuits.gui import CircuitsApp, CircuitsWindow

from . import CircuitsWidgetTest


class RunCircuitsWindow(CircuitsWidgetTest):
  """Tests for 'CircuitsApp' and 'CircuitsWindow'."""

  __application_type__ = CircuitsApp

  def setUp(self) -> None:
    """Closing a window must not quit the application the tests run
    in."""
    super().setUp()
    self.app.setQuitOnLastWindowClosed(False)

  def openWindow(self) -> CircuitsWindow:
    """The window, shown live, paused."""
    window = CircuitsWindow()
    self.showLive(window)
    if window.running:
      window.togglePlay()
    return window

  def run_opens_running(self) -> None:
    """It opens on the standard circuit, running; 'Pause' stops it,
    'Play' runs it again."""
    window = CircuitsWindow()
    self.showLive(window)
    bar = window.toolBar
    self.assertEqual(window.windowTitle(), 'Circuits')
    self.assertTrue(window.running)
    self.assertEqual(bar.playButton.text, 'Pause')
    self.assertEqual(bar.speedSlider.speed, 1.0)
    self.click(bar.playButton)
    self.assertFalse(window.running)
    self.assertEqual(window.status.text, 'Paused')
    self.click(bar.playButton)
    self.assertTrue(window.running)
    window.close()

  def run_switch_closed(self) -> None:
    """The switch closed in the panel lets the current through: the lamp
    takes power and the capacitor charges; 'Reset' empties it."""
    window = self.openWindow()
    view, panel = window.circuitView, window.panel
    view.select(('part', 1))
    self.assertEqual(panel.kind, 'switch')
    self.assertTrue(panel.openButton.checked)
    self.click(panel.closedButton)
    self.assertTrue(window.circuit.parts[1].closed)
    window.advance(1.2)
    self.assertGreater(window.run.currents[2], 0.0)
    self.assertGreater(window.run.drops[3], 3.0)
    self.assertIn('Voltage across', panel.words())
    self.click(window.toolBar.resetButton)
    self.assertEqual(window.run.time, 0.0)
    self.assertAlmostEqual(window.run.drops[3], 0.0, 12)
    window.close()

  def run_add_parts(self) -> None:
    """A part is added two steps right of the node selected, selected;
    between the two nodes selected; in the place of the wire selected."""
    window = self.openWindow()
    bar, view, panel = window.toolBar, window.circuitView, window.panel
    view.select(('node', 3))
    self.click(bar.resistorButton)
    circuit = window.circuit
    self.assertEqual(circuit.nodes[-1], Node(10.0, 4.0))
    self.assertEqual(circuit.parts[-1], Resistor(3, 5, 100.0))
    self.assertEqual(view.selected, ('part', 6))
    self.assertEqual(panel.kind, 'resistor')
    panel.resistanceField.value = 47.0
    panel.resistanceField.valueEdited.emit(47.0)
    self.assertEqual(window.circuit.parts[-1].resistance, 47.0)
    view.select(('node', 5))
    view.toggle(('node', 4))
    self.click(bar.wireButton)
    self.assertEqual(window.circuit.parts[-1], Wire(5, 4))
    view.select(('part', 5))
    self.click(bar.ammeterButton)
    self.assertEqual(window.circuit.parts[5], Ammeter(4, 0))
    self.assertEqual(len(window.circuit.parts), 8)
    window.close()

  def run_speed(self) -> None:
    """The speed slider runs the circuit slower or faster, the curves
    showing as much less or more time; a speed set elsewhere moves the
    slider to it."""
    window = self.openWindow()
    slider = window.toolBar.speedSlider
    self.assertTrue(slider.isVisible())
    for _ in range(6):
      self.key(slider, Qt.Key.Key_Left)
    self.assertEqual(window.speed, 0.01)
    self.assertEqual(slider.valueText(), '1/100×')
    self.assertAlmostEqual(window.voltageCurve.window, 0.2, 12)
    self.assertEqual(window.voltageCurve.timeScale()[1], 'ms')
    window.advance(0.0)
    self.assertIn('1/100 of real time', window.status.details)
    self.key(slider, Qt.Key.Key_End)
    self.assertEqual(window.speed, 10.0)
    window.advance(0.0)
    self.assertIn('10× real time', window.status.details)
    window.setSpeed(0.001)
    self.assertEqual(slider.speed, 0.001)
    self.assertEqual(slider.stop, 0)
    window.close()

  def run_add_transistor(self) -> None:
    """A transistor goes with its base at the node selected, its
    collector and emitter a step above and below two steps to the
    right; with three nodes selected, it joins them, collector, base
    and emitter in turn."""
    window = self.openWindow()
    bar, view = window.toolBar, window.circuitView
    view.select(('node', 3))
    self.click(bar.transistorButton)
    circuit = window.circuit
    part = circuit.parts[-1]
    self.assertIsInstance(part, Transistor)
    self.assertEqual(part.base, 3)
    self.assertEqual(circuit.nodes[part.first], Node(10.0, 5.0))
    self.assertEqual(circuit.nodes[part.second], Node(10.0, 3.0))
    self.assertEqual(window.panel.kind, 'transistor')
    self.assertEqual(window.run.regions[-1], 'off')
    view.select(('node', 0))
    view.toggle(('node', 1))
    view.toggle(('node', 4))
    self.click(bar.transistorButton)
    self.assertEqual(window.circuit.parts[-1][:3], (0, 4, 1))
    window.close()

  def run_diode_turned(self) -> None:
    """A diode added from a node is set in the panel and turned round by
    its button."""
    window = self.openWindow()
    bar, view, panel = window.toolBar, window.circuitView, window.panel
    view.select(('node', 3))
    self.click(bar.diodeButton)
    self.assertEqual(window.circuit.parts[-1], Diode(3, 5, 0.7))
    self.assertEqual(panel.kind, 'diode')
    self.click(panel.turnButton)
    self.assertEqual(window.circuit.parts[-1], Diode(5, 3, 0.7))
    window.close()

  def run_examples(self) -> None:
    """The examples' menu has each example; chosen, one is shown anew,
    its word on what to do in the panel, at its speed, settled as long
    as it asks."""
    window = self.openWindow()
    menu = window.examplesMenu()
    self.assertEqual([a.text() for a in menu.actions()],
                     [example.name for example in EXAMPLES])
    menu.actions()[5].trigger()
    self.assertEqual(window.panel.note, EXAMPLES[5].hint)
    self.assertEqual(len(window.circuit.parts), 10)
    self.assertEqual(window.run.time, 0.0)
    self.assertEqual(window.speed, 1.0)
    menu.actions()[7].trigger()
    self.assertEqual(window.speed, 0.001)
    self.assertAlmostEqual(window.run.time, 1.0, 12)
    self.assertEqual(window.run.regions[8], 'active')
    self.assertIsNone(window.circuitView.selected)
    window.close()

  def run_short_circuit(self) -> None:
    """A battery shorted by wire is said to be a short circuit, in the
    status and the panel."""
    window = self.openWindow()
    nodes = (Node(0.0, 0.0), Node(0.0, 2.0), Node(2.0, 2.0))
    window.setCircuit(Circuit(nodes, (Source(1, 0, 4.5, 0.0, 0.0),
                                      Wire(1, 2), Wire(2, 0))))
    self.assertEqual(window.status.text, 'Short circuit')
    self.assertIn('Short circuit', window.panel.words())
    window.close()
