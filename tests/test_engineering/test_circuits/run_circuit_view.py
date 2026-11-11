"""
RunCircuitView covers 'CircuitView': the circuit fits the view; parts
in parallel are drawn aside; a click selects a node or a part; a node
dragged goes to the grid, and dropped on another node joins it; Delete
removes what is selected; the dots move with the current; a
transistor's base lead selects it, its own dots moving with the base
current; a chip's box selects it, and dragged moves all its pins.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QPointF, Qt

from worQt.engineering.circuits import Bit, Chip, Circuit, Node, Probe
from worQt.engineering.circuits import Run, Switch
from worQt.engineering.circuits._examples import switching
from worQt.engineering.circuits.gui import CircuitView

from . import CircuitsWidgetTest


class RunCircuitView(CircuitsWidgetTest):
  """Tests for 'CircuitView'."""

  def openView(self) -> CircuitView:
    """The view of the standard circuit, shown live."""
    view = CircuitView()
    view.resize(1000, 700)
    self.showLive(view)
    return view

  def nodePixel(self, view: CircuitView, index: int) -> QPointF:
    """Where the node of 'index' is drawn."""
    return view.toScreen(*view.circuit.nodes[index])

  def run_fits(self) -> None:
    """Every node is drawn inside the view; the voltmeter, beside the
    capacitor, is drawn a step and a half aside, outside the loop."""
    view = self.openView()
    for index in range(len(view.circuit.nodes)):
      pixel = self.nodePixel(view, index)
      self.assertTrue(0 < pixel.x() < view.width())
      self.assertTrue(0 < pixel.y() < view.height())
    self.assertEqual(len(view.pathOf(3)), 2)
    path = view.pathOf(4)
    self.assertEqual(len(path), 4)
    scale = view.place()[0]
    self.assertAlmostEqual(path[1].x() - path[0].x(), 1.5 * scale, 6)

  def run_click_selects(self) -> None:
    """A click selects the node or the part under it; Ctrl and a click
    adds; on nothing, nothing."""
    view = self.openView()
    self.click(view, self.nodePixel(view, 2))
    self.assertEqual(view.selected, ('node', 2))
    middle, _, _, _ = view.bodyOf(2)
    self.click(view, middle)
    self.assertEqual(view.selected, ('part', 2))
    view.toggle(('node', 0))
    self.assertEqual(view.selection, (('part', 2), ('node', 0)))
    self.click(view, QPointF(5.0, view.height() - 5.0))
    self.assertIsNone(view.selected)

  def run_drag_and_join(self) -> None:
    """A node dragged goes to the point of the grid under the mouse; on
    another node, dropped, it joins it."""
    view = self.openView()
    spy = self.spy(view.circuitEdited)
    start = self.nodePixel(view, 2)
    self.press(view, start)
    self.move(view, view.toScreen(4.0, 5.0))
    self.release(view, view.toScreen(4.0, 5.0))
    self.assertEqual(view.circuit.nodes[2], Node(4.0, 5.0))
    self.assertGreater(len(spy), 0)
    self.press(view, self.nodePixel(view, 2))
    self.move(view, self.nodePixel(view, 1))
    self.assertEqual(view.merging, 1)
    self.release(view, self.nodePixel(view, 1))
    self.assertEqual(len(view.circuit.nodes), 4)
    self.assertEqual(view.selected, ('node', 1))
    self.assertEqual(view.circuit.parts[1].__class__.__name__, 'Lamp')

  def run_delete(self) -> None:
    """Delete removes the part selected; a node selected goes with its
    parts."""
    view = self.openView()
    view.select(('part', 4))
    self.key(view, Qt.Key.Key_Delete)
    self.assertEqual(len(view.circuit.parts), 5)
    view.select(('node', 2))
    self.key(view, Qt.Key.Key_Delete)
    self.assertEqual(len(view.circuit.nodes), 4)
    self.assertEqual(len(view.circuit.parts), 3)

  def run_flow(self) -> None:
    """With the switch closed and the circuit run on, the dots move along
    the parts the current flows through, not the voltmeter."""
    view = self.openView()
    circuit = Circuit().withPart(1, Switch(1, 2, True))
    view.circuit = circuit
    run = Run(circuit)
    view.run = run
    run.advance(0.02)
    view.flow(1.0)
    self.assertTrue(view.flowing(2))
    self.assertFalse(view.flowing(4))
    self.assertGreater(view.offsets[2], 0.0)
    self.assertEqual(view.offsets[4], 0.0)
    self.assertAlmostEqual(view.shownCurrent(0), run.currents[2], 12)

  def run_transistor(self) -> None:
    """A click on a transistor's base lead selects it; its label goes
    on the side away from its base; switched on, dots move along its
    base lead."""
    view = self.openView()
    circuit = switching().withPart(7, Switch(2, 8, True))
    view.circuit = circuit
    run = Run(circuit)
    view.run = run
    base, meets = view.baseLead(5)
    self.assertIsNone(view.baseLead(4))
    middle = QPointF((base.x() + meets.x()) / 2, base.y())
    self.click(view, middle)
    self.assertEqual(view.selected, ('part', 5))
    nx, _ = view.labelSide(5)
    self.assertGreater(nx, 0.5)
    run.advance(0.02)
    view.flow(1.0)
    count = len(circuit.parts)
    self.assertTrue(view.flowing(count + 5))
    self.assertFalse(view.flowing(count + 4))
    self.assertGreater(view.offsets[count + 5], 0.0)

  def run_chip(self) -> None:
    """A click in a chip's box selects it; its box dragged takes all its
    pins along, to the grid."""
    view = self.openView()
    nodes = (Node(0.0, 0.0), Node(0.0, 2.0), Node(0.0, 3.0),
             Node(4.0, 2.0))
    circuit = Circuit(nodes, (Bit(1, 0, True, 'A'), Bit(2, 0, True, 'B'),
                              Chip('NAND', (1, 2, 3)), Probe(3, 0, 'Q')))
    view.circuit = circuit
    view.run = Run(circuit)
    box = view.chipBox(2)
    self.click(view, box.center())
    self.assertEqual(view.selected, ('part', 2))
    start = box.center()
    scale = view.place()[0]
    self.press(view, start)
    self.move(view, start + QPointF(0.0, -scale))
    self.release(view, start + QPointF(0.0, -scale))
    moved = view.circuit.nodes
    self.assertEqual(moved[3], Node(4.0, 3.0))
    self.assertEqual(moved[1], Node(0.0, 3.0))
    self.assertEqual(moved[0], Node(0.0, 0.0))
